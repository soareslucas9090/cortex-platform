from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import DiaSemana


class Rota(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import RotaBusiness
    from .helpers import RotaHelpers
    from .rules import RotaRules

    business_class = RotaBusiness
    helper_class = RotaHelpers
    rules_class = RotaRules

    percurso = models.ForeignKey(
        'percursos.Percurso',
        on_delete=models.PROTECT,
        related_name='rotas',
        verbose_name='Percurso',
    )
    horario_saida = models.TimeField('Horário de saída')
    dia_semana = models.CharField(
        'Dia da semana',
        max_length=10,
        choices=DiaSemana.choices,
    )
    quantidade_vagas = models.PositiveIntegerField('Quantidade de vagas')
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Rota'
        verbose_name_plural = 'Rotas'
        ordering = ['dia_semana', 'horario_saida', 'percurso__apelido']
        constraints = [
            models.UniqueConstraint(
                fields=['percurso', 'dia_semana', 'horario_saida'],
                name='rotas_rota_percurso_dia_horario_unico',
            ),
            models.CheckConstraint(
                condition=models.Q(quantidade_vagas__gte=1),
                name='rotas_rota_vagas_minimo_1',
            ),
        ]

    def __str__(self):
        return f'{self.percurso} — {self.get_dia_semana_display()} {self.horario_saida}'
