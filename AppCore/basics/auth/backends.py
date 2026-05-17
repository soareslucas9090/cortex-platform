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

        # Detectar tipo de identificador e normalizar
        if '@' in login:
            identificador = login.strip().lower()
            campo = 'email'
        else:
            identificador = normalizar_cpf(login)
            campo = 'cpf'

        try:
            user = UserModel._default_manager.get(**{campo: identificador})
        except (UserModel.DoesNotExist, NotFoundException):
            # Executar set_password para mitigar timing attacks (Django convention)
            UserModel().set_password(password)
            return None
        except Exception:
            logger.exception(
                'Erro inesperado durante autenticação. campo=%s', campo
            )
            return None

        if not self.user_can_authenticate(user):
            return None

        if user.check_password(password):
            return user

        return None
