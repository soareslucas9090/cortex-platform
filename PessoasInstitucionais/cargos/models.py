from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class Cargo(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import CargoBusiness
    from .helpers import CargoHelpers
    from .rules import CargoRules

    business_class = CargoBusiness
    helper_class = CargoHelpers
    rules_class = CargoRules

    nome = models.CharField('Nome', max_length=255, unique=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'
        ordering = ['nome']

    def __str__(self):
        return self.nome
