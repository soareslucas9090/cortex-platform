from AppCore.core.rules.rules import ModelInstanceRules


class ServidorRules(ModelInstanceRules):

    def usuario_sem_perfil_servidor(self, usuario_pk) -> bool:
        """Valida que o usuário ainda não possui perfil de servidor."""
        from .models import Servidor
        if Servidor.objects.filter(pk=usuario_pk).exists():
            self.return_exception('Este usuário já possui perfil de servidor.')
        return True

    def cargo_ativo(self, cargo) -> bool:
        """Valida que o cargo informado está ativo."""
        if not cargo.ativo:
            self.return_exception('Não é possível vincular um cargo inativo ao servidor.')
        return True

    def pode_desativar(self) -> bool:
        """Servidor só pode ser desativado se estiver ativo."""
        if not self.object_instance.ativo:
            self.return_exception('O servidor já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Servidor só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O servidor já está ativo.')
        return True
