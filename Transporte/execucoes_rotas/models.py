from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin
from AppCore.core.state.state_mixin import ModelStateMixin

from .choices import StatusExecucaoRota
from .state import ESTADOS_EXECUCAO_ROTA


class ExecucaoRota(
    ModelStateMixin,
    ModelHelperMixin,
    ModelBusinessMixin,
    ModelRulesMixin,
    BasicModel,
):
    from .business import ExecucaoRotaBusiness
    from .helpers import ExecucaoRotaHelpers
    from .rules import ExecucaoRotaRules

    business_class = ExecucaoRotaBusiness
    helper_class = ExecucaoRotaHelpers
    rules_class = ExecucaoRotaRules
    state_class_builder = ESTADOS_EXECUCAO_ROTA

    rota = models.ForeignKey(
        'rotas.Rota',
        on_delete=models.PROTECT,
        related_name='execucoes',
        verbose_name='Rota',
    )
    data_execucao = models.DateField('Data da execução')
    data_hora_saida = models.DateTimeField('Data e hora de saída')
    quantidade_vagas = models.PositiveIntegerField('Quantidade de vagas')
    status = models.IntegerField(
        'Status',
        choices=StatusExecucaoRota.choices,
        default=StatusExecucaoRota.ABERTA,
    )
    chamada_tickets_concluida = models.BooleanField(
        'Chamada de tickets concluída',
        default=False,
    )
    monitoramento_iniciado_em = models.DateTimeField(
        'Monitoramento iniciado em',
        null=True,
        blank=True,
    )
    chamada_concluida_em = models.DateTimeField(
        'Chamada concluída em',
        null=True,
        blank=True,
    )
    finalizada_em = models.DateTimeField(
        'Finalizada em',
        null=True,
        blank=True,
    )
    chamada_ausentes_codigos = models.JSONField(
        'Códigos ausentes da chamada',
        default=list,
        blank=True,
    )

    class Meta:
        verbose_name = 'Execução de rota'
        verbose_name_plural = 'Execuções de rotas'
        ordering = ['data_hora_saida', 'rota_id']
        constraints = [
            models.UniqueConstraint(
                fields=['rota', 'data_execucao'],
                name='execucao_rota_unica_por_data',
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade_vagas__gte=1),
                name='execucao_rota_vagas_minimo_1',
            ),
        ]

    def __str__(self):
        return f'{self.rota} — {self.data_hora_saida:%d/%m/%Y %H:%M}'

