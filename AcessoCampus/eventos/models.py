from django.db import models

from AppCore.basics.models.models import BasicModel
from AppCore.core.business.business_mixin import ModelBusinessMixin
from AppCore.core.helpers.helpers_mixin import ModelHelperMixin
from AppCore.core.rules.rules_mixin import ModelRulesMixin


class EventoAcesso(ModelHelperMixin, ModelBusinessMixin, ModelRulesMixin, BasicModel):
    from .business import EventoAcessoBusiness
    from .helpers import EventoAcessoHelpers
    from .rules import EventoAcessoRules

    business_class = EventoAcessoBusiness
    helper_class = EventoAcessoHelpers
    rules_class = EventoAcessoRules

    solicitacao = models.OneToOneField(
        'acesso_campus_solicitacoes.SolicitacaoAcesso',
        on_delete=models.PROTECT,
        related_name='evento',
        verbose_name='Solicitação',
    )
    aluno = models.ForeignKey(
        'alunos.Aluno', on_delete=models.PROTECT, related_name='eventos_acesso', verbose_name='Aluno'
    )
    grupo_portaria_id = models.UUIDField('Grupo da portaria', db_index=True)
    tipo = models.ForeignKey(
        'acesso_campus_tipos.TipoAutorizacaoAcesso',
        on_delete=models.PROTECT,
        related_name='eventos_acesso',
        verbose_name='Tipo de movimento',
    )
    data_acesso = models.DateField('Data autorizada', db_index=True)
    hora_prevista = models.TimeField('Horário autorizado')
    turma_origem = models.CharField('Turma de origem', max_length=50, blank=True)
    aluno_nome = models.CharField('Nome do aluno', max_length=255)
    curso_nome = models.CharField('Nome do curso', max_length=255)
    matricula = models.CharField('Matrícula', max_length=50, blank=True)
    expirado_em = models.DateTimeField('Expirado em', null=True, blank=True)

    class Meta:
        verbose_name = 'Evento de acesso'
        verbose_name_plural = 'Eventos de acesso'
        ordering = ['data_acesso', 'hora_prevista', 'aluno_nome']
        indexes = [models.Index(fields=['grupo_portaria_id', 'data_acesso'], name='evento_grupo_data_idx')]

    def __str__(self):
        return f'{self.aluno_nome} — {self.tipo.nome} em {self.data_acesso}'
