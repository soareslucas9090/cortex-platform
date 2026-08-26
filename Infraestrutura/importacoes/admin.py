from django.contrib import admin

from AppCore.basics.admin import ReadOnlyModelAdmin

from .models import ImportacaoLote


@admin.register(ImportacaoLote)
class ImportacaoLoteAdmin(ReadOnlyModelAdmin):
    list_display = (
        'pk',
        'status',
        'total_linhas',
        'linhas_processadas',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('pk',)
    readonly_fields = (
        'arquivo',
        'status',
        'total_linhas',
        'linhas_processadas',
        'resultado_json',
        'created_at',
        'updated_at',
    )
    fieldsets = (
        (
            'Processamento',
            {
                'fields': (
                    'arquivo',
                    'status',
                    'total_linhas',
                    'linhas_processadas',
                    'resultado_json',
                ),
            },
        ),
        ('Auditoria', {'fields': ('created_at', 'updated_at')}),
    )
