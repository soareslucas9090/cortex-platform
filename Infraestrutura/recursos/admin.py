from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Recurso


@admin.register(Recurso)
class RecursoAdmin(AtivoModelAdmin):
    list_display = ('codigo', 'tipo', 'sala', 'foto', 'em_avaria', 'ativo', 'created_at')
    list_filter = ('tipo', 'ativo', 'em_avaria', 'sala__bloco')
    search_fields = ('codigo', 'descricao', 'sala__nome')
    readonly_fields = ('foto',)
    ordering = ('codigo',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Recurso().business.criar_recurso(
                    codigo=obj.codigo,
                    tipo=obj.tipo,
                    sala_id=obj.sala_id,
                    descricao=obj.descricao,
                    em_avaria=obj.em_avaria,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
