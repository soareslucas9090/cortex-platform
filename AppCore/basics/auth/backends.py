"""
Backend de Autenticação — Email ou CPF

Detecta automaticamente se o identificador enviado é um e-mail ou um CPF
e autentica o usuário correspondente.

Regras:
  - Se `login` contém '@' → trata como e-mail (normaliza com strip + lowercase)
  - Caso contrário        → trata como CPF (remove pontos, hífen e espaços)

Adicione ao settings.py:

    AUTHENTICATION_BACKENDS = [
        'AppCore.basics.auth.backends.EmailOrCpfBackend',
        'django.contrib.auth.backends.ModelBackend',   # fallback para admin Django
    ]

O model de usuário deve possuir os campos `email` e `cpf` para que o backend
funcione plenamente. Até que o model concreto seja criado, tentativas de login
por CPF resultam em None (campo inexistente → capturado e logado internamente).
"""

import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from AppCore.common.util.util import normalizar_cpf
from AppCore.core.exceptions.exceptions import NotFoundException

from Identidade.matriculas.choices import SituacaoMatricula

logger = logging.getLogger(__name__)


class EmailOrCpfBackend(ModelBackend):
    """
    Backend de autenticação que aceita e-mail ou CPF como identificador.

    Recebe o parâmetro ``login`` (em vez do USERNAME_FIELD padrão do Django).
    Toda falha de autenticação retorna ``None`` — o motivo nunca é exposto
    ao chamador (OWASP A07 — Falhas de Identificação e Autenticação).
    """

    def authenticate(self, request, login=None, password=None, **kwargs):
        if login is None or password is None:
            return None

        UserModel = get_user_model()
        user = None

        # Detectar tipo de identificador e buscar correspondente
        if '@' in login:
            identificador = login.strip().lower()
            try:
                user = UserModel._default_manager.get(email=identificador)
            except (UserModel.DoesNotExist, NotFoundException):
                pass
            except Exception:
                logger.exception('Erro inesperado durante busca por email.')
        else:
            # 1. Tentar busca por CPF se o valor puder ser um CPF válido (11 dígitos)
            cpf_normalizado = normalizar_cpf(login)
            if len(cpf_normalizado) == 11:
                try:
                    user = UserModel._default_manager.get(cpf=cpf_normalizado)
                except (UserModel.DoesNotExist, NotFoundException):
                    pass
                except Exception:
                    logger.exception('Erro inesperado durante busca por CPF.')

            # 2. Se não encontrou por CPF, tentar busca por matrícula ativa (situação = 1)
            if not user:
                try:
                    user = UserModel._default_manager.filter(
                        matriculas__matricula=login,
                        matriculas__situacao=SituacaoMatricula.ATIVA,
                    ).first()
                except Exception:
                    logger.exception('Erro inesperado durante busca por matrícula.')

        if not user:
            # Executar set_password para mitigar timing attacks (Django convention)
            UserModel().set_password(password)
            return None

        if not self.user_can_authenticate(user):
            return None

        if user.check_password(password):
            return user

        return None
