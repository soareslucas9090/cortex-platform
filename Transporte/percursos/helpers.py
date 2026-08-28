from AppCore.core.helpers.helpers import ModelInstanceHelpers


class PercursoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os percursos ativos."""
        from .models import Percurso
        return Percurso.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os percursos inativos."""
        from .models import Percurso
        return Percurso.objects.filter(ativo=False)
