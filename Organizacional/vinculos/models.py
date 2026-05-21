from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class SetorVinculo(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import SetorVinculoBusiness
    from .helpers import SetorVinculoHelpers

    business_class = SetorVinculoBusiness
    helper_class = SetorVinculoHelpers

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='setor_vinculos',
        verbose_name='Usuário',
    )
    setor = models.ForeignKey(
        'setores.Setor',
        on_delete=models.CASCADE,
        related_name='vinculos',
        verbose_name='Setor',
    )
    funcao = models.ForeignKey(
        'funcoes.Funcao',
        on_delete=models.PROTECT,
        related_name='vinculos',
        verbose_name='Função',
    )
    responsavel = models.BooleanField('Responsável', default=False)

    class Meta:
        verbose_name = 'Vínculo de Setor'
        verbose_name_plural = 'Vínculos de Setor'
        ordering = ['setor', 'usuario']

    def __str__(self):
        return f'{self.usuario} — {self.setor} ({self.funcao.sigla})'
