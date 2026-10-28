from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class PermissaoFuncaoAcessoCampus(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PermissaoFuncaoAcessoCampusBusiness
    from .helpers import PermissaoFuncaoAcessoCampusHelpers
    from .rules import PermissaoFuncaoAcessoCampusRules

    business_class = PermissaoFuncaoAcessoCampusBusiness
    helper_class = PermissaoFuncaoAcessoCampusHelpers
    rules_class = PermissaoFuncaoAcessoCampusRules

    funcao = models.OneToOneField(
        'funcoes.Funcao',
        on_delete=models.PROTECT,
        related_name='permissao_acesso_campus',
        verbose_name='Função',
    )
    solicitar = models.BooleanField('Solicitar', default=False)
    analisar_solicitacoes = models.BooleanField('Analisar solicitações', default=False)
    operar_portaria = models.BooleanField('Operar portaria', default=False)
    visualizar_historico = models.BooleanField('Visualizar histórico', default=False)

    class Meta:
        verbose_name = 'Permissão de acesso ao campus por função'
        verbose_name_plural = 'Permissões de acesso ao campus por função'
        ordering = ['funcao__papel_funcao']

    def __str__(self):
        return f'Acesso ao campus — {self.funcao}'


class PermissaoUsuarioAcessoCampus(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import PermissaoUsuarioAcessoCampusBusiness
    from .helpers import PermissaoUsuarioAcessoCampusHelpers
    from .rules import PermissaoUsuarioAcessoCampusRules

    business_class = PermissaoUsuarioAcessoCampusBusiness
    helper_class = PermissaoUsuarioAcessoCampusHelpers
    rules_class = PermissaoUsuarioAcessoCampusRules

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='permissao_acesso_campus',
        verbose_name='Usuário',
    )
    solicitar = models.BooleanField('Solicitar', default=False)
    analisar_solicitacoes = models.BooleanField('Analisar solicitações', default=False)
    operar_portaria = models.BooleanField('Operar portaria', default=False)
    visualizar_historico = models.BooleanField('Visualizar histórico', default=False)

    class Meta:
        verbose_name = 'Permissão de acesso ao campus por usuário'
        verbose_name_plural = 'Permissões de acesso ao campus por usuário'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'Acesso ao campus — {self.usuario}'
