from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import StatusJustificativa


class Justificativa(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import JustificativaBusiness
    from .helpers import JustificativaHelpers
    from .rules import JustificativaRules

    business_class = JustificativaBusiness
    helper_class = JustificativaHelpers
    rules_class = JustificativaRules

    aluno = models.ForeignKey(
        'alunos.Aluno',
        on_delete=models.PROTECT,
        related_name='justificativas_transporte',
        verbose_name='Aluno',
    )
    strikes_cobertos = models.ManyToManyField(
        'strikes.Strike',
        related_name='justificativas',
        verbose_name='Strikes cobertos',
    )
    texto = models.TextField('Justificativa')
    status = models.IntegerField(
        'Status',
        choices=StatusJustificativa.choices,
        default=StatusJustificativa.PENDENTE,
    )
    observacao_analise = models.TextField('Observação da análise', blank=True)
    analisada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='justificativas_transporte_analisadas',
        verbose_name='Analisada por',
        null=True,
        blank=True,
    )
    analisada_em = models.DateTimeField('Analisada em', null=True, blank=True)

    class Meta:
        verbose_name = 'Justificativa'
        verbose_name_plural = 'Justificativas'
        ordering = ['-created_at']

    def __str__(self):
        return f'Justificativa de {self.aluno} — {self.get_status_display()}'

