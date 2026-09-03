from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin
from Identidade.usuarios.models import Usuario

from .choices import FormaIngresso, SituacaoAluno


class Aluno(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import AlunoBusiness
    from .helpers import AlunoHelpers
    from .rules import AlunoRules

    business_class = AlunoBusiness
    helper_class = AlunoHelpers
    rules_class = AlunoRules

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='aluno',
        primary_key=True,
        verbose_name='Usuário',
    )
    ira = models.FloatField(
        'IRA',
        default=0.0,
    )
    situacao = models.IntegerField(
        'Situação',
        choices=SituacaoAluno.choices,
        default=SituacaoAluno.MATRICULADO,
    )
    forma_ingresso = models.IntegerField(
        'Forma de Ingresso',
        choices=FormaIngresso.choices,
        default=FormaIngresso.VESTIBULAR,
    )
    ativo = models.BooleanField('Ativo', default=True)
    faltas = models.PositiveSmallIntegerField(
        'Faltas de transporte',
        default=0,
        help_text='Quantidade de strikes ativos no transporte universitário.',
    )
    is_bloqueado = models.BooleanField(
        'Bloqueado no transporte',
        default=False,
        help_text='Indica bloqueio por três ou mais faltas ativas no transporte.',
    )

    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['usuario__nome']

    def __str__(self):
        return f'{self.usuario.nome} (Aluno)'
