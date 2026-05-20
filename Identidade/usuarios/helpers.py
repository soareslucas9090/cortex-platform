from AppCore.core.helpers.helpers import ModelInstanceHelpers


class UsuarioHelpers(ModelInstanceHelpers):
    """
    Queries e utilitários do domínio Usuários.
    Fornece consultas reutilizáveis sobre o model Usuario.
    Chamada exclusivamente pela camada Business.
    """

    def listar_ativos(self):
        """Retorna todos os usuários ativos do sistema."""
        from .models import Usuario
        return Usuario.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os usuários inativos do sistema."""
        from .models import Usuario
        return Usuario.objects.filter(ativo=False)
