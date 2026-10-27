from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Curso


@admin.register(Curso)
class CursoAdmin(AtivoModelAdmin):
    list_display = ('nome', 'codigo_curso', 'setor', 'ativo', 'created_at')
    list_filter = ('ativo', 'setor')
    search_fields = ('nome', 'codigo_curso', 'setor__sigla', 'setor__nome')
    autocomplete_fields = ('setor',)
    ordering = ('nome',)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['setor'].required = True
        return form

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Curso().business.criar_curso(
                    nome=obj.nome,
                    codigo_curso=obj.codigo_curso,
                    setor_id=obj.setor_id,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {}
        for field in form.changed_data:
            valor = form.cleaned_data[field]
            if field == 'setor':
                dados['setor_id'] = valor.pk if valor else None
            else:
                dados[field] = valor
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
