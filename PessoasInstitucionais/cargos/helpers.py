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

    def obter_por_nome_normalizado(self, nome):
        """Retorna o cargo cujo nome coincide após normalização de texto, ou None."""
        from AppCore.common.util.util import normalizar_chave_texto
        from .models import Cargo

        chave = normalizar_chave_texto(nome)
        if not chave:
            return None
        for cargo in Cargo.objects.all():
            if normalizar_chave_texto(cargo.nome) == chave:
                return cargo
        return None
