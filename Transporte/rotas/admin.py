from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .choices import anotacao_ordem_dia_semana
from .models import Rota


@admin.register(Rota)
class RotaAdmin(AtivoModelAdmin):
    list_display = ('percurso', 'dia_semana', 'horario_saida', 'quantidade_vagas', 'ativo', 'created_at')
    list_filter = ('ativo', 'dia_semana', 'percurso')
    search_fields = ('percurso__apelido',)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('percurso')
            .annotate(_ordem_dia=anotacao_ordem_dia_semana())
            .order_by('_ordem_dia', 'horario_saida', 'percurso__apelido')
        )

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Rota().business.criar_rota(
                    percurso_id=obj.percurso_id,
                    horario_saida=obj.horario_saida,
                    dia_semana=obj.dia_semana,
                    quantidade_vagas=obj.quantidade_vagas,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if 'percurso' in dados:
            dados['percurso_id'] = dados.pop('percurso').pk
        ativo_novo = dados.pop('ativo', None)
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
        if ativo_novo is not None:
            obj.refresh_from_db()
            if ativo_novo:
                run_business(lambda: obj.business.reativar())
            else:
                run_business(lambda: obj.business.desativar())
