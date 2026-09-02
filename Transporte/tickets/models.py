import uuid

from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin
from AppCore.core.state.state_mixin import ModelStateMixin

from .choices import StatusTicket
from .state import ESTADOS_TICKET


class Ticket(
    ModelStateMixin,
    ModelHelperMixin,
    ModelBusinessMixin,
    ModelRulesMixin,
    BasicModel,
):
    from .business import TicketBusiness
    from .helpers import TicketHelpers
    from .rules import TicketRules

    business_class = TicketBusiness
    helper_class = TicketHelpers
    rules_class = TicketRules
    state_class_builder = ESTADOS_TICKET

    codigo = models.UUIDField('Código público', default=uuid.uuid4, unique=True, editable=False)
    execucao_rota = models.ForeignKey(
        'execucoes_rotas.ExecucaoRota',
        on_delete=models.PROTECT,
        related_name='tickets',
        verbose_name='Execução da rota',
    )
    aluno = models.ForeignKey(
        'alunos.Aluno',
        on_delete=models.PROTECT,
        related_name='tickets_transporte',
        verbose_name='Aluno',
    )
    status = models.IntegerField('Status', choices=StatusTicket.choices)
    reservado_em = models.DateTimeField('Reservado em', null=True, blank=True)
    entrou_em_espera_em = models.DateTimeField('Entrou em espera em', null=True, blank=True)
    cancelado_em = models.DateTimeField('Cancelado em', null=True, blank=True)
    embarcado_em = models.DateTimeField('Embarcado em', null=True, blank=True)
    ausente_em = models.DateTimeField('Ausente em', null=True, blank=True)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['execucao_rota', 'aluno'],
                condition=~models.Q(status=StatusTicket.CANCELADO),
                name='ticket_ativo_unico_aluno_execucao',
            ),
        ]
        indexes = [
            models.Index(fields=['execucao_rota', 'status'], name='ticket_execucao_status_idx'),
            models.Index(fields=['status', 'entrou_em_espera_em'], name='ticket_fila_ordem_idx'),
        ]

    def __str__(self):
        return f'{self.codigo} — {self.aluno} — {self.get_status_display()}'

