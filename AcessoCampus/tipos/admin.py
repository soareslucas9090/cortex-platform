from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import TipoAutorizacaoAcesso


@admin.register(TipoAutorizacaoAcesso)
class TipoAutorizacaoAcessoAdmin(AtivoModelAdmin):
    list_display = ('nome', 'ativo', 'eh_base', 'created_at')
    list_filter = ('ativo', 'eh_base')
    search_fields = ('nome',)
    ordering = ('nome',)
    readonly_fields = ('eh_base',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: TipoAutorizacaoAcesso().business.criar_tipo(
                    nome=obj.nome,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
            if field != 'eh_base'
        }
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
