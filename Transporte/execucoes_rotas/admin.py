from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import ExecucaoRota


@admin.register(ExecucaoRota)
class ExecucaoRotaAdmin(ReadOnlyModelAdmin):
    list_display = ['id', 'rota', 'data_hora_saida', 'quantidade_vagas', 'status']
    list_filter = ['status', 'data_execucao']
    search_fields = ['rota__percurso__apelido']
