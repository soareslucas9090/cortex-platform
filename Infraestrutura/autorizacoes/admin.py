from django.contrib import admin

from .models import Autorizacao


@admin.register(Autorizacao)
class AutorizacaoAdmin(admin.ModelAdmin):
    list_display = (
        'beneficiario',
        'sala',
        'recurso',
        'data_inicio',
        'data_fim',
        'revogado_em',
        'concedente',
    )
    list_filter = ('revogado_em', 'data_inicio')
    search_fields = (
        'beneficiario__nome',
        'beneficiario__cpf',
        'sala__nome',
        'recurso__codigo',
    )
    raw_id_fields = ('beneficiario', 'concedente', 'revogador', 'sala', 'recurso')
    ordering = ('-data_inicio',)
