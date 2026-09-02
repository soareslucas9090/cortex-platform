from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class PermissaoFuncaoTransporte(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PermissaoFuncaoTransporteBusiness
    from .helpers import PermissaoFuncaoTransporteHelpers
    from .rules import PermissaoFuncaoTransporteRules

    business_class = PermissaoFuncaoTransporteBusiness
    helper_class = PermissaoFuncaoTransporteHelpers
    rules_class = PermissaoFuncaoTransporteRules

    funcao = models.OneToOneField(
        'funcoes.Funcao',
        on_delete=models.PROTECT,
        related_name='permissao_transporte',
        verbose_name='Função',
    )
    conferir = models.BooleanField('Conferir', default=False)

    class Meta:
        verbose_name = 'Permissão de Transporte por Função'
        verbose_name_plural = 'Permissões de Transporte por Função'
        ordering = ['funcao__papel_funcao']

    def __str__(self):
        return f'Transporte — {self.funcao}'


class PermissaoUsuarioTransporte(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PermissaoUsuarioTransporteBusiness
    from .helpers import PermissaoUsuarioTransporteHelpers
    from .rules import PermissaoUsuarioTransporteRules

    business_class = PermissaoUsuarioTransporteBusiness
    helper_class = PermissaoUsuarioTransporteHelpers
    rules_class = PermissaoUsuarioTransporteRules

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='permissao_transporte',
        verbose_name='Usuário',
    )
    conferir = models.BooleanField('Conferir', default=False)

    class Meta:
        verbose_name = 'Permissão de Transporte por Usuário'
        verbose_name_plural = 'Permissões de Transporte por Usuário'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'Transporte — {self.usuario}'
