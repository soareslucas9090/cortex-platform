from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin

from .choices import TipoRecurso


class Recurso(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import RecursoBusiness
    from .helpers import RecursoHelpers

    business_class = RecursoBusiness
    helper_class = RecursoHelpers

    codigo = models.CharField('Código', max_length=50, unique=True)
    tipo = models.CharField(
        'Tipo',
        max_length=20,
        choices=TipoRecurso.choices,
    )
    sala = models.ForeignKey(
        'salas.Sala',
        on_delete=models.PROTECT,
        related_name='recursos',
        null=True,
        blank=True,
        verbose_name='Sala',
    )
    descricao = models.CharField('Descrição', max_length=500, blank=True, default='')
    em_avaria = models.BooleanField('Em avaria', default=False)
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} ({self.get_tipo_display()})'

    @property
    def estado_derivado(self):
        """Estado operacional derivado: avaria → emprestado → reservado → disponível."""
        return self.helpers.obter_estado_derivado()
