from AppCore.core.helpers.helpers import ModelInstanceHelpers


class RotaHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todas as rotas ativas."""
        from .models import Rota
        return Rota.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todas as rotas inativas."""
        from .models import Rota
        return Rota.objects.filter(ativo=False)
