from AppCore.core.helpers.helpers import ModelInstanceHelpers


class TerceirizadoHelpers(ModelInstanceHelpers):

    def listar_ativos(self):
        """Retorna todos os terceirizados ativos."""
        from .models import Terceirizado
        return Terceirizado.objects.filter(ativo=True).select_related('usuario', 'empresa_instituicao')

    def listar_inativos(self):
        """Retorna todos os terceirizados inativos."""
        from .models import Terceirizado
        return Terceirizado.objects.filter(ativo=False).select_related('usuario', 'empresa_instituicao')

    def buscar_por_usuario(self, usuario_pk):
        """Retorna o terceirizado associado a um usuário, se existir."""
        from .models import Terceirizado
        return Terceirizado.objects.filter(pk=usuario_pk).select_related('usuario', 'empresa_instituicao').first()

    def listar_por_empresa(self, empresa_pk):
        """Retorna todos os terceirizados vinculados a uma empresa_instituicao/instituição."""
        from .models import Terceirizado
        return Terceirizado.objects.filter(empresa_instituicao_id=empresa_pk).select_related('usuario', 'empresa_instituicao')
