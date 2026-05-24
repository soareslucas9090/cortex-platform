from AppCore.core.helpers.helpers import ModelInstanceHelpers


class AlunoCursoHelpers(ModelInstanceHelpers):

    def obter_vinculos_por_aluno(self, aluno_id: int):
        from .models import AlunoCurso
        return AlunoCurso.objects.filter(aluno_id=aluno_id).select_related('curso')

    def obter_vinculos_por_curso(self, curso_id: int):
        from .models import AlunoCurso
        return AlunoCurso.objects.filter(curso_id=curso_id).select_related('aluno__usuario')
