from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class Terceirizado(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import TerceirizadoBusiness
    from .helpers import TerceirizadoHelpers
    from .rules import TerceirizadoRules

    business_class = TerceirizadoBusiness
    helper_class = TerceirizadoHelpers
    rules_class = TerceirizadoRules

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='terceirizado',
        primary_key=True,
        verbose_name='Usuário',
    )
    empresa_instituicao = models.ForeignKey(
        'empresas_instituicoes.EmpresaInstituicao',
        on_delete=models.PROTECT,
        related_name='terceirizados',
        verbose_name='Empresa/Instituição',
    )
    cargo = models.ForeignKey(
        'cargos.Cargo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='terceirizados',
        verbose_name='Cargo',
    )
    data_inicio = models.DateField(
        'Data de Início',
        null=True,
        blank=True,
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
        return f'{self.usuario.nome} - {self.empresa_instituicao.nome}'
