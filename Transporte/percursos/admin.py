from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Percurso


@admin.register(Percurso)
class PercursoAdmin(AtivoModelAdmin):
    list_display = ('apelido', 'ativo', 'created_at')
    list_filter = ('ativo',)
    search_fields = ('apelido', 'descricao')
    ordering = ('apelido',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Percurso().business.criar_percurso(
                    apelido=obj.apelido,
                    descricao=obj.descricao,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        ativo_novo = dados.pop('ativo', None)
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
        if ativo_novo is not None:
            obj.refresh_from_db()
            if ativo_novo:
                run_business(lambda: obj.business.reativar())
            else:
                run_business(lambda: obj.business.desativar())
