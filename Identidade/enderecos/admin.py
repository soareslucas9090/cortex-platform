from django.contrib import admin

from AppCore.basics.admin import CortexModelAdmin, run_business

from .models import Endereco


@admin.register(Endereco)
class EnderecoAdmin(CortexModelAdmin):
    list_display = (
        'usuario',
        'logradouro',
        'numero',
        'bairro',
        'cidade',
        'estado',
        'cep',
    )
    list_filter = ('estado', 'cidade')
    search_fields = (
        'usuario__nome',
        'usuario__cpf',
        'logradouro',
        'bairro',
        'cidade',
        'cep',
    )
    autocomplete_fields = ('usuario',)
    ordering = ('usuario__nome',)

    def save_model(self, request, obj, form, change):
        usuario = form.cleaned_data['usuario']
        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
            if field != 'usuario'
        } if change else {
            key: form.cleaned_data[key]
            for key in (
                'logradouro',
                'numero',
                'complemento',
                'bairro',
                'cep',
                'cidade',
                'estado',
            )
        }
        run_business(lambda: usuario.business.salvar_endereco(dados))

    def has_delete_permission(self, request, obj=None):
        return False
