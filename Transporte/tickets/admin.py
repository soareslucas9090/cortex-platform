from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(ReadOnlyModelAdmin):
    list_display = ['codigo', 'aluno', 'execucao_rota', 'status', 'created_at']
    list_filter = ['status', 'execucao_rota__data_execucao']
    search_fields = ['codigo', 'aluno__usuario__nome', 'aluno__usuario__cpf']
