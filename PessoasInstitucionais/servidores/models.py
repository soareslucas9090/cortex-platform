from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin

from .choices import CategoriaServidor


class Servidor(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import ServidorBusiness
    from .helpers import ServidorHelpers

    business_class = ServidorBusiness
    helper_class = ServidorHelpers

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='servidor',
        primary_key=True,
        verbose_name='Usuário',
    )
    cargo = models.ForeignKey(
        'cargos.Cargo',
        on_delete=models.PROTECT,
        related_name='servidores',
        verbose_name='Cargo',
    )
    categoria = models.IntegerField(
        'Categoria',
        choices=CategoriaServidor.choices,
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Servidor'
        verbose_name_plural = 'Servidores'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'{self.usuario.nome} - {self.cargo.nome}'
