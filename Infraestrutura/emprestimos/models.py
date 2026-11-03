from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin
from AppCore.core.state.state_mixin import ModelStateMixin

from .choices import OrigemContaColetiva, StatusSolicitacaoTrocaTitular
from .state import ESTADOS_SOLICITACAO_TROCA_TITULAR


class Emprestimo(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import EmprestimoBusiness
    from .helpers import EmprestimoHelpers
    from .rules import EmprestimoRules

    business_class = EmprestimoBusiness
    helper_class = EmprestimoHelpers
    rules_class = EmprestimoRules

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='emprestimos_solicitados',
        verbose_name='Solicitante',
    )
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='emprestimos_registrados',
        verbose_name='Responsável',
    )
    origem_conta_coletiva = models.CharField(
        'Origem da conta coletiva',
        max_length=30,
        choices=OrigemContaColetiva.choices,
        null=True,
        blank=True,
        editable=False,
        db_index=True,
        help_text='Tipo da conta coletiva que realizou a operação, congelado na criação.',
    )
    retirada_em = models.DateTimeField('Retirada em')
    observacao = models.TextField('Observação', blank=True, default='')

    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['solicitante__nome', '-retirada_em']

    def __str__(self):
        return f'Empréstimo #{self.pk} — {self.solicitante}'

    @property
    def ativo(self) -> bool:
        """Empréstimo ativo enquanto houver item sem devolução."""
        return self.helper.esta_ativo()

    @property
    def atrasado(self) -> bool:
        """Sinalização para o frontend: aberto há mais de 24 horas."""
        return self.helper.esta_atrasado()


class ItemEmprestimo(BasicModel):
    emprestimo = models.ForeignKey(
        'emprestimos.Emprestimo', on_delete=models.PROTECT, related_name='itens', verbose_name='Empréstimo'
    )
    recurso = models.ForeignKey(
        'recursos.Recurso', on_delete=models.PROTECT, related_name='itens_emprestimo', verbose_name='Recurso'
    )
    devolvido_em = models.DateTimeField('Devolvido em', null=True, blank=True)

    class Meta:
        verbose_name = 'Item de empréstimo'
        verbose_name_plural = 'Itens de empréstimo'
        ordering = ['recurso__codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['recurso'],
                condition=models.Q(devolvido_em__isnull=True),
                name='emprestimos_item_recurso_unico_aberto',
            )
        ]

    def __str__(self):
        return f'{self.recurso} — empréstimo #{self.emprestimo_id}'

    @property
    def ativo(self) -> bool:
        return self.devolvido_em is None


class SolicitacaoTrocaTitular(ModelStateMixin, ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import SolicitacaoTrocaTitularBusiness
    from .helpers import SolicitacaoTrocaTitularHelpers
    from .rules import SolicitacaoTrocaTitularRules

    business_class = SolicitacaoTrocaTitularBusiness
    helper_class = SolicitacaoTrocaTitularHelpers
    rules_class = SolicitacaoTrocaTitularRules
    state_class_builder = ESTADOS_SOLICITACAO_TROCA_TITULAR

    emprestimo = models.ForeignKey(
        'emprestimos.Emprestimo',
        on_delete=models.PROTECT,
        related_name='solicitacoes_troca_titular',
        verbose_name='Empréstimo original',
    )
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitacoes_troca_titular_enviadas',
        verbose_name='Solicitante',
    )
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='solicitacoes_troca_titular_recebidas',
        verbose_name='Destinatário',
    )
    status = models.IntegerField(
        'Status', choices=StatusSolicitacaoTrocaTitular.choices, default=StatusSolicitacaoTrocaTitular.PENDENTE
    )
    observacao = models.TextField('Observação', blank=True, default='')
    respondido_em = models.DateTimeField('Respondido em', null=True, blank=True)
    novo_emprestimo = models.OneToOneField(
        'emprestimos.Emprestimo',
        on_delete=models.PROTECT,
        related_name='solicitacao_troca_titular_origem',
        verbose_name='Novo empréstimo',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Solicitação de troca de titular'
        verbose_name_plural = 'Solicitações de troca de titular'
        ordering = ['-created_at', '-pk']
        constraints = [
            models.UniqueConstraint(
                fields=['emprestimo'],
                condition=models.Q(status=StatusSolicitacaoTrocaTitular.PENDENTE),
                name='soltroca_pendente_unica_emprestimo',
            )
        ]
        indexes = [
            models.Index(fields=['destinatario', 'status', 'created_at'], name='soltroca_dest_status_idx'),
            models.Index(fields=['solicitante', 'status', 'created_at'], name='soltroca_soli_status_idx'),
            models.Index(fields=['emprestimo', 'status'], name='soltroca_emp_status_idx'),
        ]

    def __str__(self):
        return f'Solicitação #{self.pk} — {self.get_status_display()}'
