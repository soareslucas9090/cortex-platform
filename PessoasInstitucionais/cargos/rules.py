from AppCore.core.rules.rules import ModelInstanceRules


class CargoRules(ModelInstanceRules):

    def nome_unico(self, nome: str, excluir_id=None) -> bool:
        """Valida que o nome do cargo não está em uso."""
        from .models import Cargo
        qs = Cargo.objects.filter(nome__iexact=nome)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um cargo cadastrado com esse nome.')
        return True

    def pode_desativar(self) -> bool:
        """Cargo só pode ser desativado se não estiver em uso."""
        if not self.object_instance.ativo:
            self.return_exception('O cargo já está inativo.')
        
        # Futuramente: checar vínculos com servidores
        # if hasattr(self.object_instance, 'servidor_set') and self.object_instance.servidor_set.exists():
        #     self.return_exception('Não é possível desativar um cargo com servidores vinculados.')
            
        return True

    def pode_reativar(self) -> bool:
        """Cargo só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O cargo já está ativo.')
        return True
