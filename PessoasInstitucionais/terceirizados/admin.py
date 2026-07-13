from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Terceirizado


@admin.register(Terceirizado)
class TerceirizadoAdmin(AtivoModelAdmin):
    list_display = (
        'usuario',
        'empresa_instituicao',
        'cargo',
        'data_inicio',
        'data_fim',
        'ativo',
        'created_at',
    )
    list_filter = ('ativo', 'empresa_instituicao', 'cargo')
    search_fields = (
        'usuario__nome',
        'usuario__cpf',
        'empresa_instituicao__nome',
        'cargo__nome',
    )
    autocomplete_fields = ('usuario', 'empresa_instituicao', 'cargo')
    date_hierarchy = 'data_inicio'
    ordering = ('usuario__nome',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('usuario', 'empresa_instituicao', 'cargo')
        )

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Terceirizado().business.criar_terceirizado(
                    usuario_pk=obj.usuario_id,
                    empresa_pk=obj.empresa_instituicao_id,
                    cargo_pk=obj.cargo_id,
                    data_inicio=obj.data_inicio,
                    data_fim=obj.data_fim,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {}
        if 'empresa_instituicao' in form.changed_data:
            dados['empresa_instituicao_pk'] = obj.empresa_instituicao_id
        if 'cargo' in form.changed_data:
            dados['cargo_pk'] = obj.cargo_id
        for field in ('data_inicio', 'data_fim', 'ativo'):
            if field in form.changed_data:
                dados[field] = form.cleaned_data[field]

        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
