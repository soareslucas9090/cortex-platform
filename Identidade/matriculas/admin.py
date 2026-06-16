from django.contrib import admin

from AppCore.basics.admin import CortexModelAdmin, run_business

from .models import Matricula


@admin.register(Matricula)
class MatriculaAdmin(CortexModelAdmin):
    list_display = ('matricula', 'usuario', 'situacao', 'created_at')
    list_filter = ('situacao',)
    search_fields = ('matricula', 'usuario__nome', 'usuario__cpf')
    autocomplete_fields = ('usuario',)
    ordering = ('matricula',)
    actions = ('desativar_selecionados',)

    @admin.action(description='Marcar matrículas como inativas')
    def desativar_selecionados(self, request, queryset):
        for matricula in queryset:
            run_business(lambda current=matricula: current.business.desativar())

    def has_delete_permission(self, request, obj=None):
        return False
