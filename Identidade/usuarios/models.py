from django.db import models

from AppCore.basics.models.models import BasicModel, BaseManagerUser
from AppCore.basics.models.user_model import AbstractBaseAppUser
from AppCore.common.util.util import normalizar_cpf
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


def _normalizar_email(email):
    if not email:
        return email
    return email.strip().lower()


class UsuarioManager(BaseManagerUser):

    def create_user(self, cpf, password=None, **extra_fields):
        if not cpf:
            raise ValueError('O CPF é obrigatório.')

        cpf = normalizar_cpf(cpf)

        email = extra_fields.get('email')
        if email:
            extra_fields['email'] = _normalizar_email(email)

        user = self.model(cpf=cpf, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cpf, password, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(cpf, password, **extra_fields)


class Usuario(ModelHelperMixin, ModelBusinessMixin, AbstractBaseAppUser):
    from .business import UsuarioBusiness
    from .helpers import UsuarioHelpers

    business_class = UsuarioBusiness
    helper_class = UsuarioHelpers

    email = models.EmailField(
        'E-mail',
        unique=True,
        null=True,
        blank=True,
    )
    cpf = models.CharField(
        'CPF',
        max_length=11,
        unique=True,
    )
    foto = models.ImageField(
        'Foto',
        upload_to='usuarios/fotos/',
        null=True,
        blank=True,
    )
    deficiencia = models.TextField(
        'Deficiência / necessidade especial',
        blank=True,
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']
