from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel


class Endereco(BasicModel):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='endereco',
        verbose_name='Usuário',
    )
    logradouro = models.CharField('Logradouro', max_length=255)
    numero = models.CharField('Número', max_length=20)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cep = models.CharField('CEP', max_length=8)
    cidade = models.CharField('Cidade', max_length=100)
    estado = models.CharField('Estado', max_length=2)

    class Meta:
        verbose_name = 'Endereço'
        verbose_name_plural = 'Endereços'

    def __str__(self):
        return f'Endereço de {self.usuario}'
