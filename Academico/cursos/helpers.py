from AppCore.core.helpers.helpers import ModelInstanceHelpers


class CursoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os cursos ativos."""
        from .models import Curso
        return Curso.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os cursos inativos."""
        from .models import Curso
        return Curso.objects.filter(ativo=False)
