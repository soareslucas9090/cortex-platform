from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class PermissaoFuncaoInfraestrutura(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PermissaoFuncaoInfraestruturaBusiness
    from .helpers import PermissaoFuncaoInfraestruturaHelpers
    from .rules import PermissaoFuncaoInfraestruturaRules

    business_class = PermissaoFuncaoInfraestruturaBusiness
    helper_class = PermissaoFuncaoInfraestruturaHelpers
    rules_class = PermissaoFuncaoInfraestruturaRules

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


class PermissaoUsuarioInfraestrutura(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PermissaoUsuarioInfraestruturaBusiness
    from .helpers import PermissaoUsuarioInfraestruturaHelpers
    from .rules import PermissaoUsuarioInfraestruturaRules

    business_class = PermissaoUsuarioInfraestruturaBusiness
    helper_class = PermissaoUsuarioInfraestruturaHelpers
    rules_class = PermissaoUsuarioInfraestruturaRules

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='permissao_infraestrutura',
        verbose_name='Usuário',
    )
    operar = models.BooleanField('Operar', default=False)
    cadastrar = models.BooleanField('Cadastrar', default=False)
    autorizar = models.BooleanField('Autorizar', default=False)
    retirada_irrestrita = models.BooleanField('Retirada irrestrita', default=False)

    class Meta:
        verbose_name = 'Permissão de Infraestrutura por Usuário'
        verbose_name_plural = 'Permissões de Infraestrutura por Usuário'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'Infraestrutura — {self.usuario}'
