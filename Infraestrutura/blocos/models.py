from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class Bloco(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import BlocoBusiness
    from .helpers import BlocoHelpers

    business_class = BlocoBusiness
    helper_class = BlocoHelpers

    nome = models.CharField('Nome', max_length=255)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Bloco'
        verbose_name_plural = 'Blocos'
        ordering = ['nome']

    def __str__(self):
        return self.nome
