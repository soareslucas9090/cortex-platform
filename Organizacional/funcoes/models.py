from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class Funcao(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import FuncaoBusiness
    from .helpers import FuncaoHelpers

    business_class = FuncaoBusiness
    helper_class = FuncaoHelpers

    papel_funcao = models.CharField('Papel/Função', max_length=255, unique=True)
    descricao = models.CharField('Descrição', max_length=255)
    e_gratificada = models.BooleanField('É gratificada', default=False)
    exige_aluno = models.BooleanField('Exige Aluno', default=False)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Função'
        verbose_name_plural = 'Funções'
        ordering = ['papel_funcao']

    def __str__(self):
        return self.papel_funcao
