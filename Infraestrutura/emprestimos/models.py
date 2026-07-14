from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


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
    retirada_em = models.DateTimeField('Retirada em')
    observacao = models.TextField('Observação', blank=True, default='')

    class Meta:
        verbose_name = 'Empréstimo'
        verbose_name_plural = 'Empréstimos'
        ordering = ['-retirada_em']

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
        'emprestimos.Emprestimo',
        on_delete=models.PROTECT,
        related_name='itens',
        verbose_name='Empréstimo',
    )
    recurso = models.ForeignKey(
        'recursos.Recurso',
        on_delete=models.PROTECT,
        related_name='itens_emprestimo',
        verbose_name='Recurso',
    )
    devolvido_em = models.DateTimeField('Devolvido em', null=True, blank=True)

    class Meta:
        verbose_name = 'Item de empréstimo'
        verbose_name_plural = 'Itens de empréstimo'
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['recurso'],
                condition=models.Q(devolvido_em__isnull=True),
                name='emprestimos_item_recurso_unico_aberto',
            ),
        ]

    def __str__(self):
        return f'{self.recurso} — empréstimo #{self.emprestimo_id}'

    @property
    def ativo(self) -> bool:
        return self.devolvido_em is None
