from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class Setor(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import SetorBusiness
    from .helpers import SetorHelpers
    from .rules import SetorRules

    business_class = SetorBusiness
    helper_class = SetorHelpers
    rules_class = SetorRules

    nome = models.CharField('Nome', max_length=255)
    sigla = models.CharField('Sigla', max_length=20, unique=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['nome']

    def __str__(self):
        return f'{self.sigla} — {self.nome}'
