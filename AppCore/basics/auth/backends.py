"""
Backend de Autenticação — Email, CPF ou Matrícula

Detecta automaticamente se o identificador enviado é um e-mail, um CPF
ou uma matrícula ativa e autentica o usuário correspondente.

Regras:
  - Se `login` contém '@' → trata como e-mail (normaliza com strip + lowercase)
  - Caso contrário, se 11 dígitos → trata como CPF (remove pontos, hífen e espaços)
  - Caso contrário → trata como matrícula ativa em AlunoCurso, Servidor ou Terceirizado

Após localizar o usuário, exige CPF ou matrícula válida para permitir login.

Adicione ao settings.py:

    AUTHENTICATION_BACKENDS = [
        'AppCore.basics.auth.backends.EmailOrCpfBackend',
        'django.contrib.auth.backends.ModelBackend',   # fallback para admin Django
    ]
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from AppCore.common.util.util import normalizar_cpf
from AppCore.core.exceptions.exceptions import NotFoundException
from Identidade.usuarios.models import Usuario

logger = logging.getLogger(__name__)


class EmailOrCpfBackend(ModelBackend):
    """
    Backend de autenticação que aceita e-mail, CPF ou matrícula como identificador.

    Recebe o parâmetro ``login`` (em vez do USERNAME_FIELD padrão do Django).
    Toda falha de autenticação retorna ``None`` — o motivo nunca é exposto
    ao chamador (OWASP A07 — Falhas de Identificação e Autenticação).
    """

    def authenticate(self, request, login=None, password=None, **kwargs):
        if login is None or password is None:
            return None

        UserModel = get_user_model()
        user = None

        if '@' in login:
            identificador = login.strip().lower()
            try:
                user = UserModel._default_manager.get(email=identificador)
            except (UserModel.DoesNotExist, NotFoundException):
                pass
            except Exception:
                logger.exception('Erro inesperado durante busca por email.')
        else:
            cpf_normalizado = normalizar_cpf(login)
            if len(cpf_normalizado) == 11:
                try:
                    user = UserModel._default_manager.get(cpf=cpf_normalizado)
                except (UserModel.DoesNotExist, NotFoundException):
                    pass
                except Exception:
                    logger.exception('Erro inesperado durante busca por CPF.')

            if not user:
                try:
                    user = Usuario().helper.buscar_por_matricula_valida(login)
                except UserModel.MultipleObjectsReturned:
                    logger.error(
                        'Múltiplos usuários com a mesma matrícula ativa durante login.',
                    )
                except Exception:
                    logger.exception('Erro inesperado durante busca por matrícula.')

        if not user:
            UserModel().set_password(password)
            return None

        if not self._usuario_elegivel_para_login(user):
            UserModel().set_password(password)
            return None

        if not self.user_can_authenticate(user):
            return None

        if user.check_password(password):
            return user

        return None

    def _usuario_elegivel_para_login(self, user) -> bool:
        """Exige CPF ou matrícula válida em uma das três fontes."""
        if user.cpf:
            return True
        return user.helper.tem_matricula_valida()
