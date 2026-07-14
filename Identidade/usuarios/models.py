from django.db import models

from AppCore.basics.models.models import BasicModel, BaseManagerUser
from AppCore.basics.models.user_model import AbstractBaseAppUser
from AppCore.common.util.util import normalizar_cpf
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin
from AppCore.core.users_permissions.user_permission_mixin import UserModelPermissionMixin
from .choices import PERMISSAO_CORTEX_EDITAR_TUDO, PERMISSAO_CORTEX_LER_TUDO
from .permissions import UsuarioPermissions


def _normalizar_email(email):
    if not email:
        return email
    return email.strip().lower()


class UsuarioManager(BaseManagerUser):

    def create_user(self, cpf=None, password=None, **extra_fields):
        if cpf:
            cpf = normalizar_cpf(cpf)

            if not len(cpf) == 11:
                raise ValueError('CPF deve ter 11 dígitos')

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


class TipoDeficiencia(models.TextChoices):
    DEFICIENCIA_INTELECTUAL = 'deficiencia_intelectual', 'Deficiência Intelectual'
    DEFICIENCIA_VISUAL = 'deficiencia_visual', 'Deficiência Visual'
    DEFICIENCIA_AUDITIVA = 'deficiencia_auditiva', 'Deficiência Auditiva'
    DEFICIENCIA_MULTIPLA = 'deficiencia_multipla', 'Deficiência Múltipla'
    DEFICIENCIA_FISICA = 'deficiencia_fisica', 'Deficiência Física'


class Usuario(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, UserModelPermissionMixin, AbstractBaseAppUser):
    from .business import UsuarioBusiness
    from .helpers import UsuarioHelpers
    from .rules import UsuarioRules

    business_class = UsuarioBusiness
    helper_class = UsuarioHelpers
    rules_class = UsuarioRules
    user_permissions_class = UsuarioPermissions

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
        null=True,
        blank=True,
    )
    foto = models.URLField(
        'Foto primária',
        max_length=500,
        null=True,
        blank=True,
        help_text='URL pública da foto vinda de sistemas externos.',
    )
    foto_secundaria = models.URLField(
        'Foto secundária',
        max_length=500,
        null=True,
        blank=True,
        help_text='Chave S3 da foto enviada pelo próprio usuário (servida via proxy da API).',
    )
    deficiencia = models.CharField(
        'Deficiência / necessidade especial',
        max_length=50,
        choices=TipoDeficiencia.choices,
        blank=True,
        null=True,
    )
    colaborador_externo = models.BooleanField(
        'Colaborador externo',
        default=False,
        help_text='Indica se o usuário é colaborador externo à instituição.',
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['nome']

    def save(self, *args, **kwargs):
        if self.cpf == '':
            self.cpf = None

        super().save(*args, **kwargs)

    def tem_acesso_elevado(self) -> bool:
        return self.permissoes.get('cortex') == PERMISSAO_CORTEX_EDITAR_TUDO

    def tem_leitura_ampla(self) -> bool:
        return self.permissoes.get('cortex') in (
            PERMISSAO_CORTEX_LER_TUDO,
            PERMISSAO_CORTEX_EDITAR_TUDO,
        )

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']


class StatusImportacao(models.TextChoices):
    EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'
    ERRO = 'ERRO', 'Erro'


class ImportacaoLote(BasicModel):
    arquivo = models.FileField('Arquivo de Importação', upload_to='importacoes/usuarios/%Y/%m/%d/')
    status = models.CharField('Status', max_length=20, choices=StatusImportacao.choices, default=StatusImportacao.EM_ANDAMENTO)
    total_linhas = models.IntegerField('Total de Linhas', default=0)
    linhas_processadas = models.IntegerField('Linhas Processadas', default=0)
    resultado_json = models.JSONField('Resultado/Erros', null=True, blank=True)

    class Meta:
        verbose_name = 'Importação de Lote de Usuários'
        verbose_name_plural = 'Importações de Lote de Usuários'
        ordering = ['-created_at']

    def __str__(self):
        return f"Importação {self.pk} - {self.get_status_display()} ({self.linhas_processadas}/{self.total_linhas})"
