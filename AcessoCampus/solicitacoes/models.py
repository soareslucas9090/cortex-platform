from django.conf import settings
from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin

from .choices import OrigemSolicitacaoAcesso, StatusSolicitacaoAcesso, TipoSolicitacaoAcesso


class SolicitacaoAcesso(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import SolicitacaoAcessoBusiness
    from .helpers import SolicitacaoAcessoHelpers
    from .rules import SolicitacaoAcessoRules

    business_class = SolicitacaoAcessoBusiness
    helper_class = SolicitacaoAcessoHelpers
    rules_class = SolicitacaoAcessoRules

    aluno = models.ForeignKey(
        'alunos.Aluno',
        on_delete=models.PROTECT,
        related_name='solicitacoes_acesso',
        verbose_name='Aluno',
    )
    aluno_curso = models.ForeignKey(
        'aluno_cursos.AlunoCurso',
        on_delete=models.PROTECT,
        related_name='solicitacoes_acesso',
        verbose_name='Vínculo aluno-curso',
    )
    origem = models.IntegerField('Origem', choices=OrigemSolicitacaoAcesso.choices)
    tipo = models.IntegerField('Tipo', choices=TipoSolicitacaoAcesso.choices)
    status = models.IntegerField(
        'Status',
        choices=StatusSolicitacaoAcesso.choices,
        default=StatusSolicitacaoAcesso.PENDENTE,
    )
    data_acesso = models.DateField('Data da autorização de acesso')
    hora_solicitada = models.TimeField('Horário solicitado', null=True, blank=True)
    hora_autorizada = models.TimeField('Horário autorizado', null=True, blank=True)
    motivo = models.CharField('Motivo', max_length=255)
    justificativa = models.TextField('Justificativa', blank=True)
    observacao_avaliacao = models.TextField('Observação da avaliação', blank=True)
    avaliada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_acesso_avaliadas',
        verbose_name='Avaliada por',
    )
    avaliada_em = models.DateTimeField('Avaliada em', null=True, blank=True)
    liberado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitacoes_acesso_liberadas',
        verbose_name='Liberado por',
    )
    lote_id = models.UUIDField('Lote', null=True, blank=True)
    turma_origem = models.CharField('Turma de origem', max_length=50, blank=True)
    aluno_nome = models.CharField('Nome do aluno', max_length=255)
    curso_nome = models.CharField('Nome do curso', max_length=255)
    matricula = models.CharField('Matrícula', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Solicitação de acesso'
        verbose_name_plural = 'Solicitações de acesso'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['aluno', 'data_acesso', 'tipo'],
                condition=models.Q(status=StatusSolicitacaoAcesso.ACEITA),
                name='uniq_acesso_aceito_aluno_data_tipo',
            ),
        ]

    def __str__(self):
        return f'{self.aluno_nome} — {self.get_tipo_display()} ({self.get_status_display()})'
