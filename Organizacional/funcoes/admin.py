from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Funcao


@admin.register(Funcao)
class FuncaoAdmin(AtivoModelAdmin):
    list_display = (
        'papel_funcao',
        'categoria',
        'descricao',
        'e_gratificada',
        'exige_aluno',
        'ativo',
        'created_at',
    )
    list_filter = ('ativo', 'categoria', 'e_gratificada', 'exige_aluno')
    search_fields = ('papel_funcao', 'descricao')
    ordering = ('papel_funcao',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Funcao().business.criar_funcao(
                    papel_funcao=obj.papel_funcao,
                    categoria=obj.categoria,
                    descricao=obj.descricao,
                    e_gratificada=obj.e_gratificada,
                    exige_aluno=obj.exige_aluno,
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
