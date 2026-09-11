from django.contrib import admin

from AppCore.basics.admin import AtivoModelAdmin, run_business

from .models import AlunoCurso


@admin.register(AlunoCurso)
class AlunoCursoAdmin(AtivoModelAdmin):
    list_display = ('aluno', 'curso', 'matricula', 'ano_conclusao', 'ativo', 'created_at')
    list_filter = ('ativo', 'curso', 'aluno__situacao')
    search_fields = (
        'aluno__usuario__nome',
        'aluno__usuario__cpf',
        'curso__nome',
        'curso__codigo_curso',
        'matricula',
    )
    autocomplete_fields = ('aluno', 'curso')
    ordering = ('aluno__usuario__nome', 'curso__nome')

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('aluno__usuario', 'curso')
        )

    def save_model(self, request, obj, form, change):
        if not change:
            created = run_business(
                lambda: AlunoCurso().business.criar_vinculo(
                    aluno_id=obj.aluno_id,
                    curso_id=obj.curso_id,
                    matricula=obj.matricula,
                    ano_conclusao=obj.ano_conclusao,
                    ira=obj.ira,
                    turma=obj.turma,
                    turno=obj.turno,
                    situacao_curso=obj.situacao_curso,
                    ativo=obj.ativo,
                )
            )
            obj.pk = created.pk
            return

        dados = {
            field: form.cleaned_data[field]
            for field in form.changed_data
            if field not in {'aluno', 'curso'}
        }
        if dados:
            run_business(lambda: obj.business.atualizar_dados(dados))
