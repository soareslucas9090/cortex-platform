from AppCore.core.rules.rules import ModelInstanceRules


class SetorRules(ModelInstanceRules):

    def sigla_unica(self, sigla: str, excluir_id=None) -> bool:
        """Valida que a sigla não está em uso por outro setor."""
        from .models import Setor
        qs = Setor.objects.filter(sigla=sigla)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um setor cadastrado com essa sigla.')
        return True

    def pode_desativar(self) -> bool:
        """Setor só pode ser desativado se não possuir vínculos."""
        if not self.object_instance.ativo:
            self.return_exception('O setor já está inativo.')
        if self.object_instance.vinculos.exists():
            self.return_exception('Não é possível desativar um setor com vínculos ativos.')
        return True

    def pode_reativar(self) -> bool:
        """Setor só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O setor já está ativo.')
        return True
