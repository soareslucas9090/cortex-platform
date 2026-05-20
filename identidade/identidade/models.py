from django.db import models

from AppCore.basics.models.models import BasicModel, BaseManagerUser
from AppCore.basics.models.user_model import AbstractBaseAppUser
from AppCore.common.util.util import normalizar_cpf
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin

from .choices import SituacaoMatricula


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
    # Importações locais para evitar importação circular
    from .business import UsuarioBusiness
    from .helpers import UsuarioHelpers

    business_class = UsuarioBusiness
    helper_class = UsuarioHelpers

    # Override: email vira opcional — presente para login por e-mail via EmailOrCpfBackend
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
        upload_to='identidade/fotos/',
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


class Contato(BasicModel):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='contatos',
        verbose_name='Usuário',
    )
    email_academico = models.EmailField('E-mail acadêmico', blank=True)
    email_pessoal = models.EmailField('E-mail pessoal', blank=True)
    telefone = models.CharField('Telefone', max_length=20, blank=True)

    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'

    def __str__(self):
        return f'Contato de {self.usuario}'


class Endereco(BasicModel):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='endereco',
        verbose_name='Usuário',
    )
    logradouro = models.CharField('Logradouro', max_length=255)
    numero = models.CharField('Número', max_length=20)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cep = models.CharField('CEP', max_length=8)
    cidade = models.CharField('Cidade', max_length=100)
    estado = models.CharField('Estado', max_length=2)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        return f'Endereço de {self.usuario}'


class Matricula(BasicModel):
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name='Usuário',
    )
    matricula = models.CharField('Matrícula', max_length=50)
    situacao = models.IntegerField(
        'Situação',
        choices=SituacaoMatricula.choices,
        default=SituacaoMatricula.ATIVA,
    )

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'

    def __str__(self):
        return f'{self.matricula} — {self.usuario}'
