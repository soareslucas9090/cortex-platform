from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import StatusStrike


class Strike(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import StrikeBusiness
    from .helpers import StrikeHelpers
    from .rules import StrikeRules

    business_class = StrikeBusiness
    helper_class = StrikeHelpers
    rules_class = StrikeRules

    ticket = models.OneToOneField(
        'tickets.Ticket',
        on_delete=models.PROTECT,
        related_name='strike',
        verbose_name='Ticket',
    )
    status = models.IntegerField(
        'Status',
        choices=StatusStrike.choices,
        default=StatusStrike.ATIVO,
    )

    class Meta:
        verbose_name = 'Strike'
        verbose_name_plural = 'Strikes'
        ordering = ['-created_at']

    def __str__(self):
        return f'Strike de {self.ticket.aluno} — {self.get_status_display()}'

