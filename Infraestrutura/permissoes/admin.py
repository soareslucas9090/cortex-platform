from django.contrib import admin

from AppCore.basics.admin import run_business

from .models import PermissaoFuncaoInfraestrutura


@admin.register(PermissaoFuncaoInfraestrutura)
class PermissaoFuncaoInfraestruturaAdmin(admin.ModelAdmin):
    list_display = (
        'funcao',
        'operar',
        'cadastrar',
        'autorizar',
        'retirada_irrestrita',
        'created_at',
    )
    list_filter = ('operar', 'cadastrar', 'autorizar', 'retirada_irrestrita')
    search_fields = ('funcao__papel_funcao', 'funcao__descricao')
    ordering = ('funcao__papel_funcao',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: PermissaoFuncaoInfraestrutura().business.criar_permissao(
                    funcao_id=obj.funcao_id,
                    operar=obj.operar,
                    cadastrar=obj.cadastrar,
                    autorizar=obj.autorizar,
                    retirada_irrestrita=obj.retirada_irrestrita,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if dados:
            run_business(lambda: obj.business.atualizar_capacidades(dados))
