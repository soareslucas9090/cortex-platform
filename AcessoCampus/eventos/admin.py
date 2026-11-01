from django.contrib import admin

from .models import EventoAcesso


@admin.register(EventoAcesso)
class EventoAcessoAdmin(admin.ModelAdmin):
    list_display = ("aluno_nome", "tipo", "data_acesso", "hora_prevista", "grupo_portaria_id")
    list_filter = ("tipo", "data_acesso", "expirado_em")
    search_fields = ("aluno_nome", "matricula", "turma_origem")
