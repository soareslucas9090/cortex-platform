from django.contrib import admin

from AppCore.basics.admin import CortexModelAdmin, run_business

from .models import Contato


@admin.register(Contato)
class ContatoAdmin(CortexModelAdmin):
    list_display = ('usuario', 'email_academico', 'email_pessoal', 'telefone', 'created_at')
    search_fields = (
        'usuario__nome',
        'usuario__cpf',
        'email_academico',
        'email_pessoal',
        'telefone',
    )
    autocomplete_fields = ('usuario',)
    ordering = ('usuario__nome',)

    def save_model(self, request, obj, form, change):
        if change:
            dados = {
                field: form.cleaned_data[field]
                for field in form.changed_data
            }
            run_business(lambda: obj.business.atualizar_contato(dados))
            return
        obj.save()

    def has_delete_permission(self, request, obj=None):
        return False
