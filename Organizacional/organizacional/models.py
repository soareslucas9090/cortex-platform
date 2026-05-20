from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class Setor(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import SetorBusiness
    from .helpers import SetorHelpers

    business_class = SetorBusiness
    helper_class = SetorHelpers

    nome = models.CharField('Nome', max_length=255)
    sigla = models.CharField('Sigla', max_length=20, unique=True)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'
        ordering = ['nome']

    def __str__(self):
        return f'{self.sigla} — {self.nome}'


class Funcao(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import FuncaoBusiness
    from .helpers import FuncaoHelpers

    business_class = FuncaoBusiness
    helper_class = FuncaoHelpers

    sigla = models.CharField('Sigla', max_length=20, unique=True)
    descricao = models.CharField('Descrição', max_length=255)
    e_gratificada = models.BooleanField('É gratificada', default=False)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Função'
        verbose_name_plural = 'Funções'
        ordering = ['sigla']

    def __str__(self):
        return f'{self.sigla} — {self.descricao}'


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
        Setor,
        on_delete=models.CASCADE,
        related_name='vinculos',
        verbose_name='Setor',
    )
    funcao = models.ForeignKey(
        Funcao,
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
