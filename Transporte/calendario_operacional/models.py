from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import TipoDiaCalendario


class DiaCalendarioTransporte(
    ModelHelperMixin,
    ModelBusinessMixin,
    ModelRulesMixin,
    BasicModel,
):
    from .business import DiaCalendarioTransporteBusiness
    from .helpers import DiaCalendarioTransporteHelpers
    from .rules import DiaCalendarioTransporteRules

    business_class = DiaCalendarioTransporteBusiness
    helper_class = DiaCalendarioTransporteHelpers
    rules_class = DiaCalendarioTransporteRules

    data = models.DateField('Data', unique=True)
    descricao = models.CharField('Descrição', max_length=255)
    tipo = models.CharField(
        'Tipo',
        max_length=20,
        choices=TipoDiaCalendario.choices,
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Dia do calendário de transporte'
        verbose_name_plural = 'Dias do calendário de transporte'
        ordering = ['data']

    def __str__(self):
        return f'{self.data:%d/%m/%Y} — {self.descricao}'
