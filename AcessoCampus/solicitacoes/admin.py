from django.contrib import admin

from .models import SolicitacaoAcesso


@admin.register(SolicitacaoAcesso)
class SolicitacaoAcessoAdmin(admin.ModelAdmin):
    list_display = (
        'aluno_nome',
        'tipo',
        'status',
        'data_acesso',
        'hora_autorizada',
        'origem',
        'created_at',
    )
    list_filter = ('status', 'tipo', 'origem')
    search_fields = ('aluno_nome', 'matricula', 'motivo')
    readonly_fields = (
        'aluno',
        'aluno_curso',
        'origem',
        'tipo',
        'status',
        'data_acesso',
        'hora_solicitada',
        'hora_autorizada',
        'motivo',
        'justificativa',
        'observacao_avaliacao',
        'avaliada_por',
        'avaliada_em',
        'liberado_por',
        'lote_id',
        'turma_origem',
        'aluno_nome',
        'curso_nome',
        'matricula',
    )

    def has_add_permission(self, request):
        return False
