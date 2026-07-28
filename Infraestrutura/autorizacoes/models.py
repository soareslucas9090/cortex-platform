from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class Autorizacao(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import AutorizacaoBusiness
    from .helpers import AutorizacaoHelpers
    from .rules import AutorizacaoRules

    business_class = AutorizacaoBusiness
    helper_class = AutorizacaoHelpers
    rules_class = AutorizacaoRules

    beneficiario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='autorizacoes_infraestrutura',
        verbose_name='Beneficiário',
    )
    concedente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='autorizacoes_concedidas',
        verbose_name='Concedente',
    )
    sala = models.ForeignKey(
        'salas.Sala',
        on_delete=models.PROTECT,
        related_name='autorizacoes',
        null=True,
        blank=True,
        verbose_name='Sala',
    )
    recurso = models.ForeignKey(
        'recursos.Recurso',
        on_delete=models.PROTECT,
        related_name='autorizacoes',
        null=True,
        blank=True,
        verbose_name='Recurso',
    )
    data_inicio = models.DateField('Data de início')
    data_fim = models.DateField(
        'Data de fim',
        null=True,
        blank=True,
        help_text='Nulo indica autorização permanente.',
    )
    revogado_em = models.DateTimeField('Revogado em', null=True, blank=True)
    revogador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='autorizacoes_revogadas',
        null=True,
        blank=True,
        verbose_name='Revogador',
    )
    observacao = models.TextField('Observação', blank=True, default='')

    class Meta:
        verbose_name = 'Autorização'
        verbose_name_plural = 'Autorizações'
        ordering = ['beneficiario__nome', 'recurso__codigo', 'sala__bloco__nome', 'sala__nome']

    def __str__(self):
        alvo = self.recurso or self.sala
        return f'{self.beneficiario} — {alvo}'

    @property
    def vigente(self) -> bool:
        """Indica se a autorização está ativa e dentro do período de vigência."""
        return self.helper.esta_vigente()
