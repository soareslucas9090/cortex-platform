from AppCore.core.helpers.helpers import ModelInstanceHelpers


class ServidorHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os servidores ativos."""
        from .models import Servidor
        return Servidor.objects.filter(ativo=True).select_related('usuario', 'cargo')

    def listar_inativos(self):
        """Retorna todos os servidores inativos."""
        from .models import Servidor
        return Servidor.objects.filter(ativo=False).select_related('usuario', 'cargo')

    def buscar_por_usuario(self, usuario_pk):
        """Retorna o servidor associado a um usuário, se existir."""
        from .models import Servidor
        return Servidor.objects.filter(pk=usuario_pk).select_related('usuario', 'cargo').first()
