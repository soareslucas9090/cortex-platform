from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin

from .choices import TurnoCurso


class Curso(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    from .business import CursoBusiness
    from .helpers import CursoHelpers

    business_class = CursoBusiness
    helper_class = CursoHelpers

    nome = models.CharField('Nome', max_length=255)
    codigo_curso = models.CharField('Código do Curso', max_length=50, unique=True)
    turno = models.IntegerField(
        'Turno',
        choices=TurnoCurso.choices,
        null=True,
        blank=True,
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome} ({self.codigo_curso})'
