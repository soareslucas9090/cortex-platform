from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Funcao
from .rules import FuncaoRules


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
            regras = FuncaoRules()
            run_business(lambda: regras.papel_funcao_unico(obj.papel_funcao))
            obj.save()
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
        }
        if 'papel_funcao' in dados:
            regras = FuncaoRules(object_instance=obj)
            run_business(
                lambda: regras.papel_funcao_unico(
                    dados['papel_funcao'],
                    excluir_id=obj.pk,
                )
            )
        for attr, value in dados.items():
            setattr(obj, attr, value)
        obj.save()
