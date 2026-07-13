from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class PermissaoFuncaoInfraestrutura(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import PermissaoFuncaoInfraestruturaBusiness
    from .helpers import PermissaoFuncaoInfraestruturaHelpers

    business_class = PermissaoFuncaoInfraestruturaBusiness
    helper_class = PermissaoFuncaoInfraestruturaHelpers

    funcao = models.OneToOneField(
        'funcoes.Funcao',
        on_delete=models.PROTECT,
        related_name='permissao_infraestrutura',
        verbose_name='Função',
    )
    operar = models.BooleanField('Operar', default=False)
    cadastrar = models.BooleanField('Cadastrar', default=False)
    autorizar = models.BooleanField('Autorizar', default=False)
    retirada_irrestrita = models.BooleanField('Retirada irrestrita', default=False)

    class Meta:
        verbose_name = 'Permissão de Infraestrutura por Função'
        verbose_name_plural = 'Permissões de Infraestrutura por Função'
        ordering = ['funcao__papel_funcao']

    def __str__(self):
        return f'Infraestrutura — {self.funcao}'
