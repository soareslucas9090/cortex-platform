from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin

from .choices import SituacaoMatricula


class Matricula(ModelBusinessMixin, BasicModel):
    from .business import MatriculaBusiness

    business_class = MatriculaBusiness

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matriculas',
        verbose_name='Usuário',
    )
    matricula = models.CharField('Matrícula', max_length=50)
    situacao = models.IntegerField(
        'Situação',
        choices=SituacaoMatricula.choices,
        default=SituacaoMatricula.ATIVA,
    )

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        ordering = ['matricula']
        constraints = [
            models.UniqueConstraint(
                fields=['matricula'],
                name='matriculas_matricula_unica',
            ),
        ]

    def __str__(self):
        return f'{self.matricula} — {self.usuario}'
