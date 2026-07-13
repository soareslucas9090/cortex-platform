from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Setor


@admin.register(Setor)
class SetorAdmin(AtivoModelAdmin):
    list_display = ('sigla', 'nome', 'ativo', 'created_at')
    search_fields = ('sigla', 'nome')
    ordering = ('nome',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Setor().business.criar_setor(
                    nome=obj.nome,
                    sigla=obj.sigla,
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
