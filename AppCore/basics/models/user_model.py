"""
Modelo de Usuário Base Genérico

Este módulo fornece um AbstractBaseAppUser pronto para ser herdado em qualquer projeto.
Ele inclui os campos mínimos esperados pelo AppCore (is_admin, ativo) e usa
AbstractBaseUser do Django para máxima flexibilidade no campo de login.

==============================================================================
COMO USAR
==============================================================================

1. Crie o model do seu projeto herdando de AbstractBaseAppUser:

    # meuapp/models.py
    from AppCore.basics.models.user_model import AbstractBaseAppUser
    from AppCore.basics.models.models import BaseManagerUser

    class MeuManager(BaseManagerUser):
        def create_user(self, email, password=None, **extra_fields):
            if not email:
                raise ValueError('O e-mail é obrigatório')
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save()
            return user

        def create_superuser(self, email, password, **extra_fields):
            extra_fields.setdefault('is_admin', True)
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
            return self.create_user(email, password, **extra_fields)

    class Usuario(AbstractBaseAppUser):
        objects = MeuManager()
        USERNAME_FIELD = 'email'  # já definido na base, mas pode sobrescrever
        REQUIRED_FIELDS = ['nome']

2. Defina AUTH_USER_MODEL no settings.py:

    AUTH_USER_MODEL = 'meuapp.Usuario'

==============================================================================
LOGIN POR CPF (ou outro campo)
==============================================================================

Para usar CPF no lugar de email:

    class Usuario(AbstractBaseAppUser):
        cpf = models.CharField('CPF', max_length=11, unique=True)
        USERNAME_FIELD = 'cpf'   # sobrescreve o padrão email
        REQUIRED_FIELDS = ['nome']

==============================================================================
LOGIN COM TIPO DE USUÁRIO (ex: motorista vs empresa)
==============================================================================

Use BaseTypedLoginSerializer do AppCore para login diferenciado por tipo.
Veja: AppCore/basics/auth/serializers.py

    # Exemplo: campo 'tipo' no login define qual queryset validar
    class MeuLoginSerializer(BaseTypedLoginSerializer):
        tipo_choices = ['motorista', 'empresa']

        def _validate_user_tipo(self, user, tipo):
            if tipo == 'motorista' and not hasattr(user, 'motorista'):
                raise AuthenticationFailed('Usuário não é motorista.')
            if tipo == 'empresa' and not hasattr(user, 'empresa'):
                raise AuthenticationFailed('Usuário não é empresa.')
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from simple_history.models import HistoricalRecords

from AppCore.basics.models.models import BaseManager, BaseManagerUser


class AbstractBaseAppUser(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário abstrato base para todos os projetos.

    Fornece os campos mínimos esperados pelo AppCore:
      - email (USERNAME_FIELD padrão — sobrescreva se necessário)
      - nome
      - ativo (substitui is_active do Django — compatível com auth backends que verificam is_active)
      - is_admin (flag de administrador para IsAdminPermission e IsOwnerOrAdminPermission)
      - is_staff (acesso ao admin do Django)
      - is_superuser (herda de PermissionsMixin)

    Campos de auditoria (created_at, updated_at, history) NÃO estão aqui
    porque AbstractBaseUser e BasicModel têm bases de Meta incompatíveis.
    Adicione-os no seu modelo concreto se necessário, ou herde de BasicModel
    separadamente em um modelo concreto sem `abstract = True`.
    """

    email = models.EmailField('E-mail', unique=True)
    nome = models.CharField('Nome', max_length=255)
    ativo = models.BooleanField('Ativo', default=True)
    is_admin = models.BooleanField('Administrador', default=False)
    is_staff = models.BooleanField('Staff', default=False)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    history = HistoricalRecords(inherit=True)

    objects = BaseManagerUser()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    # Mantém compatibilidade com o Django admin e auth backends,
    # que verificam is_active — delegamos para o campo 'ativo'.
    @property
    def is_active(self):
        return self.ativo

    @is_active.setter
    def is_active(self, value):
        self.ativo = value

    class Meta:
        abstract = True
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
