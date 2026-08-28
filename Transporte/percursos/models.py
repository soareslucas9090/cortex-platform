from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class Percurso(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PercursoBusiness
    from .helpers import PercursoHelpers
    from .rules import PercursoRules

    business_class = PercursoBusiness
    helper_class = PercursoHelpers
    rules_class = PercursoRules

    apelido = models.CharField('Apelido', max_length=255, unique=True)
    descricao = models.TextField('Descrição')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Percurso'
        verbose_name_plural = 'Percursos'
        ordering = ['apelido']

    def __str__(self):
        return self.apelido
