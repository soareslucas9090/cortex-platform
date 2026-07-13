from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import Curso


@admin.register(Curso)
class CursoAdmin(AtivoModelAdmin):
    list_display = ('nome', 'codigo_curso', 'turno', 'ativo', 'created_at')
    list_filter = ('ativo', 'turno')
    search_fields = ('nome', 'codigo_curso')
    ordering = ('nome',)

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: Curso().business.criar_curso(
                    nome=obj.nome,
                    codigo_curso=obj.codigo_curso,
                    turno=obj.turno,
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
