from AppCore.core.rules.rules import ModelInstanceRules


class FuncaoRules(ModelInstanceRules):

    def papel_funcao_unico(self, papel_funcao: str, excluir_id=None) -> bool:
        """Valida que o papel/função não está em uso por outra função."""
        from .models import Funcao
        qs = Funcao.objects.filter(papel_funcao=papel_funcao)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe uma função cadastrada com esse papel/função.')
        return True

    def pode_desativar(self) -> bool:
        """Função só pode ser desativada se não estiver em uso em nenhum vínculo."""
        if not self.object_instance.ativo:
            self.return_exception('A função já está inativa.')
        if self.object_instance.vinculos.exists():
            self.return_exception('Não é possível desativar uma função que está em uso.')
        return True

    def pode_reativar(self) -> bool:
        """Função só pode ser reativada se estiver inativa."""
        if self.object_instance.ativo:
            self.return_exception('A função já está ativa.')
        return True
