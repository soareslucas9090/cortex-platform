from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class Terceirizado(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import TerceirizadoBusiness
    from .helpers import TerceirizadoHelpers

    business_class = TerceirizadoBusiness
    helper_class = TerceirizadoHelpers

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='terceirizado',
        primary_key=True,
        verbose_name='Usuário',
    )
    empresa = models.ForeignKey(
        'empresas_instituicoes.EmpresaInstituicao',
        on_delete=models.PROTECT,
        related_name='terceirizados',
        verbose_name='Empresa/Instituição',
    )
    cargo_funcao = models.CharField(
        'Cargo/Função',
        max_length=255,
        help_text='Cargo ou função exercida pelo terceirizado na instituição.',
    )
    data_inicio = models.DateField(
        'Data de Início',
        help_text='Data de início do vínculo terceirizado.',
    )
    data_fim = models.DateField(
        'Data de Término',
        null=True,
        blank=True,
        help_text='Data de término do vínculo. Nulo indica vínculo em aberto.',
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Terceirizado'
        verbose_name_plural = 'Terceirizados'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'{self.usuario.nome} - {self.empresa.nome}'
