from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class TipoAutorizacaoAcesso(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import TipoAutorizacaoAcessoBusiness
    from .helpers import TipoAutorizacaoAcessoHelpers
    from .rules import TipoAutorizacaoAcessoRules

    business_class = TipoAutorizacaoAcessoBusiness
    helper_class = TipoAutorizacaoAcessoHelpers
    rules_class = TipoAutorizacaoAcessoRules

    nome = models.CharField('Nome', max_length=255, unique=True)
    ativo = models.BooleanField('Ativo', default=True)
    eh_base = models.BooleanField('Tipo-base', default=False)

    class Meta:
        verbose_name = 'Tipo de autorização'
        verbose_name_plural = 'Tipos de autorização'
        ordering = ['nome']

    def __str__(self):
        return self.nome
