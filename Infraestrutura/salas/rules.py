from AppCore.core.rules.rules import ModelInstanceRules


class SalaRules(ModelInstanceRules):

    def pode_desativar(self) -> bool:
        """Sala só pode ser desativada se estiver ativa."""
        if not self.object_instance.ativo:
            self.return_exception('A sala já está inativa.')
        return True

    def pode_reativar(self) -> bool:
        """Sala só pode ser reativada se estiver inativa."""
        if self.object_instance.ativo:
            self.return_exception('A sala já está ativa.')
        return True


class SalaSetorRules(ModelInstanceRules):

    def validar_vinculo_unico(self, sala_id, setor_id, excluir_id=None) -> bool:
        """Valida unicidade do par sala + setor."""
        from .models import SalaSetor
        qs = SalaSetor.objects.filter(sala_id=sala_id, setor_id=setor_id)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe vínculo entre esta sala e este setor.')
        return True
