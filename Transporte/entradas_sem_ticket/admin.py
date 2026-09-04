from django.contrib import admin

from .models import EntradaSemTicket


@admin.register(EntradaSemTicket)
class EntradaSemTicketAdmin(admin.ModelAdmin):
    list_display = ('cpf', 'execucao_rota', 'aluno', 'data_hora_entrada')
    search_fields = ('cpf', 'aluno__usuario__nome')
    ordering = ('-data_hora_entrada',)
