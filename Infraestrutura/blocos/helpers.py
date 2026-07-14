from AppCore.core.helpers.helpers import ModelInstanceHelpers


class BlocoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os blocos ativos."""
        from .models import Bloco
        return Bloco.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os blocos inativos."""
        from .models import Bloco
        return Bloco.objects.filter(ativo=False)
