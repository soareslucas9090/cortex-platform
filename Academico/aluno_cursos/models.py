from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from Academico.alunos.models import Aluno
from Academico.cursos.models import Curso


class AlunoCurso(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import AlunoCursoBusiness
    from .helpers import AlunoCursoHelpers
    from .rules import AlunoCursoRules

    business_class = AlunoCursoBusiness
    helper_class = AlunoCursoHelpers
    rules_class = AlunoCursoRules

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name='vinculos_cursos',
        verbose_name='Aluno',
    )
    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='alunos_vinculados',
        verbose_name='Curso',
    )
    ano_conclusao = models.IntegerField(
        'Ano de Conclusão',
        null=True,
        blank=True,
    )
    ativo = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Vínculo Aluno-Curso'
        verbose_name_plural = 'Vínculos Aluno-Curso'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.aluno} → {self.curso}'
