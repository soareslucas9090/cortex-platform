from AppCore.core.rules.rules import ModelInstanceRules


class BlocoRules(ModelInstanceRules):

    def pode_desativar(self) -> bool:
        """Bloco só pode ser desativado se estiver ativo e sem salas ativas."""
        if not self.object_instance.ativo:
            self.return_exception('O bloco já está inativo.')
        if self.object_instance.salas.filter(ativo=True).exists():
            self.return_exception('Não é possível desativar um bloco com salas ativas.')
        return True

    def pode_reativar(self) -> bool:
        """Bloco só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O bloco já está ativo.')
        return True
