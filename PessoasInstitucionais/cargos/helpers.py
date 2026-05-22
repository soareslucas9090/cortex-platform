from AppCore.core.helpers.helpers import ModelInstanceHelpers


class CargoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os cargos ativos."""
        from .models import Cargo
        return Cargo.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os cargos inativos."""
        from .models import Cargo
        return Cargo.objects.filter(ativo=False)
