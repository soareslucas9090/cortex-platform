from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class EmpresaInstituicao(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import EmpresaInstituicaoBusiness
    from .helpers import EmpresaInstituicaoHelpers
    from .rules import EmpresaInstituicaoRules

    business_class = EmpresaInstituicaoBusiness
    helper_class = EmpresaInstituicaoHelpers
    rules_class = EmpresaInstituicaoRules

    nome = models.CharField('Nome', max_length=255, unique=True)
    cnpj = models.CharField('CNPJ', max_length=14, null=True, blank=True)
    ativo = models.BooleanField('Ativa', default=True)

    class Meta:
        verbose_name = 'Empresa/Instituição'
        verbose_name_plural = 'Empresas/Instituições'
        ordering = ['nome']

    def __str__(self):
        return self.nome
