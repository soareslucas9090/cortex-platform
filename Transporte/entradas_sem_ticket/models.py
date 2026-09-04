from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class EntradaSemTicket(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import EntradaSemTicketBusiness
    from .helpers import EntradaSemTicketHelpers
    from .rules import EntradaSemTicketRules

    business_class = EntradaSemTicketBusiness
    helper_class = EntradaSemTicketHelpers
    rules_class = EntradaSemTicketRules

    execucao_rota = models.ForeignKey(
        'execucoes_rotas.ExecucaoRota',
        on_delete=models.PROTECT,
        related_name='entradas_sem_ticket',
        verbose_name='Execução da rota',
    )
    aluno = models.ForeignKey(
        'alunos.Aluno',
        on_delete=models.PROTECT,
        related_name='entradas_sem_ticket',
        verbose_name='Aluno',
    )
    cpf = models.CharField('CPF', max_length=14)
    observacao = models.TextField('Observação', blank=True, default='')
    data_hora_entrada = models.DateTimeField('Data e hora da entrada')

    class Meta:
        verbose_name = 'Entrada sem ticket'
        verbose_name_plural = 'Entradas sem ticket'
        ordering = ['data_hora_entrada']
        constraints = [
            models.UniqueConstraint(
                fields=['execucao_rota', 'aluno'],
                name='entrada_sem_ticket_unica_aluno_execucao',
            ),
        ]

    def __str__(self):
        return f'{self.cpf} — {self.execucao_rota_id}'
