from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .business import ServidorBusiness
from .models import Servidor


@admin.register(Servidor)
class ServidorAdmin(AtivoModelAdmin):
    list_display = ('usuario', 'cargo', 'categoria', 'ativo', 'created_at')
    list_filter = ('ativo', 'categoria', 'cargo')
    search_fields = ('usuario__nome', 'usuario__cpf', 'cargo__nome')
    autocomplete_fields = ('usuario', 'cargo')
    ordering = ('usuario__nome',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'cargo')

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: ServidorBusiness().criar_servidor(
                    usuario_pk=obj.usuario_id,
                    cargo_pk=obj.cargo_id,
                    categoria=obj.categoria,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {}
        if 'cargo' in form.changed_data:
            dados['cargo_pk'] = obj.cargo_id
        for field in ('categoria', 'ativo'):
            if field in form.changed_data:
                dados[field] = form.cleaned_data[field]

        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
