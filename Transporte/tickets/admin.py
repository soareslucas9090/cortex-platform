from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(ReadOnlyModelAdmin):
    # TODO | feat/tickets-transporte | Lucas Soares | 01-09-2026: Há uma maneira padronizada de registrar admins. Isso foi feito para que o admin
    # possa obedecer as mesmas regras do business. Verificar se não há nada a mais a ser implementado aqui. Vide outros admins do projeto.
    list_display = ['codigo', 'aluno', 'execucao_rota', 'status', 'created_at']
    list_filter = ['status', 'execucao_rota__data_execucao']
    search_fields = ['codigo', 'aluno__usuario__nome', 'aluno__usuario__cpf']
