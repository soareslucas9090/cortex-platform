from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin


class Contato(ModelBusinessMixin, BasicModel):
    from .business import ContatoBusiness

    business_class = ContatoBusiness

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contatos',
        verbose_name='Usuário',
    )
    email_academico = models.EmailField('E-mail acadêmico', blank=True)
    email_pessoal = models.EmailField('E-mail pessoal', blank=True)
    telefone = models.CharField('Telefone', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Contato'
        verbose_name_plural = 'Contatos'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'Contato de {self.usuario}'
