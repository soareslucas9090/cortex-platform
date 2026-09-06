from AppCore.core.helpers.helpers import ModelInstanceHelpers


class MotoristaHelpers(ModelInstanceHelpers):

    def obter_ativo_do_usuario(self, usuario):
        from .models import Motorista

        return (
            Motorista.objects.select_related('usuario')
            .filter(usuario=usuario, ativo=True, usuario__ativo=True)
            .first()
        )

    def usuario_e_motorista_ativo(self, usuario) -> bool:
        if not usuario or not getattr(usuario, 'is_authenticated', False):
            return False
        return self.obter_ativo_do_usuario(usuario) is not None
