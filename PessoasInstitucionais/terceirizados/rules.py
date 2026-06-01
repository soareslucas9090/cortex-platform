from AppCore.core.rules.rules import ModelInstanceRules


class TerceirizadoRules(ModelInstanceRules):

    def usuario_sem_perfil_terceirizado(self, usuario_pk) -> bool:
        """Valida que o usuário ainda não possui perfil de terceirizado."""
        from .models import Terceirizado
        if Terceirizado.objects.filter(pk=usuario_pk).exists():
            self.return_exception('Este usuário já possui perfil de terceirizado.')
        return True

    def empresa_ativa(self, empresa) -> bool:
        """Valida que a empresa/instituição informada está ativa."""
        if not empresa.ativo:
            self.return_exception(
                'Não é possível vincular uma empresa/instituição inativa ao terceirizado.'
            )
        return True

    def cargo_ativo(self, cargo) -> bool:
        """Valida que o cargo informado está ativo."""
        if cargo and not cargo.ativo:
            self.return_exception(
                'Não é possível vincular um cargo inativo ao terceirizado.'
            )
        return True

    def pode_desativar(self) -> bool:
        """Terceirizado só pode ser desativado se estiver ativo."""
        if not self.object_instance.ativo:
            self.return_exception('O terceirizado já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Terceirizado só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O terceirizado já está ativo.')
        return True
