from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Bloco


@admin.register(Bloco)
class BlocoAdmin(AtivoModelAdmin):
    list_display = ('nome', 'ativo', 'created_at')
    search_fields = ('nome',)
    ordering = ('nome',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Bloco().business.criar_bloco(
                    nome=obj.nome,
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
