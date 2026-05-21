from AppCore.core.helpers.helpers import ModelInstanceHelpers


class FuncaoHelpers(ModelInstanceHelpers):

    # ------------------------------------------------------------------
    # Consultas de instância (operam sobre self.object_instance = Funcao)
    # ------------------------------------------------------------------

    def esta_em_uso(self) -> bool:
        """Verifica se a função está associada a algum vínculo."""
        return self.object_instance.vinculos.exists()

    def obter_vinculos(self):
        """Retorna todos os vínculos que utilizam esta função."""
        return self.object_instance.vinculos.all()

    # ------------------------------------------------------------------
    # Consultas globais do domínio
    # ------------------------------------------------------------------

    def listar_ativas(self):
        """Retorna todas as funções ativas."""
        from .models import Funcao
        return Funcao.objects.filter(ativo=True)

    def listar_inativas(self):
        """Retorna todas as funções inativas."""
        from .models import Funcao
        return Funcao.objects.filter(ativo=False)
