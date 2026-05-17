from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import SituacaoMatricula


class UsuarioHelpers(ModelInstanceHelpers):
    """
    Queries e utilitários do domínio Identidade.
    Fornece consultas reutilizáveis sobre o UsuarioAggregate e o domínio como um todo.
    Chamada exclusivamente pela camada Business.
    """

    # ------------------------------------------------------------------
    # Consultas de instância (operam sobre self.object_instance)
    # ------------------------------------------------------------------

    def obter_contatos(self):
        """Retorna todos os contatos do usuário."""
        return self.object_instance.contatos.all()

    def tem_endereco(self) -> bool:
        """Verifica se o usuário possui endereço cadastrado."""
        return hasattr(self.object_instance, 'endereco')

    def obter_matriculas(self):
        """Retorna todas as matrículas do usuário."""
        return self.object_instance.matriculas.all()

    def obter_matriculas_ativas(self):
        """Retorna as matrículas ativas do usuário."""
        return self.object_instance.matriculas.filter(situacao=SituacaoMatricula.ATIVA)

    # ------------------------------------------------------------------
    # Consultas globais do domínio
    # Filtros explícitos por ativo — não dependem de object_instance.
    # ------------------------------------------------------------------

    def listar_ativos(self):
        """Retorna todos os usuários ativos do sistema."""
        from .models import Usuario
        return Usuario.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os usuários inativos do sistema."""
        from .models import Usuario
        return Usuario.objects.filter(ativo=False)
