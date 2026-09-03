from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin


class Motorista(ModelHelperMixin, BasicModel):
    from .helpers import MotoristaHelpers

    helper_class = MotoristaHelpers

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='motorista',
        primary_key=True,
        verbose_name='Usuário',
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Motorista'
        verbose_name_plural = 'Motoristas'
        ordering = ['usuario__nome']

    def __str__(self):
        return self.usuario.nome
