from AppCore.core.rules.rules import ModelInstanceRules


class EmpresaInstituicaoRules(ModelInstanceRules):

    def nome_unico(self, nome: str, excluir_id=None) -> bool:
        """Valida que o nome da empresa/instituição não está em uso."""
        from .models import EmpresaInstituicao
        qs = EmpresaInstituicao.objects.filter(nome__iexact=nome)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe uma empresa/instituição cadastrada com esse nome.')
        return True

    def cnpj_unico(self, cnpj: str, excluir_id=None) -> bool:
        """Valida que o CNPJ da empresa/instituição, se informado, não está em uso."""
        if not cnpj:
            return True
            
        from .models import EmpresaInstituicao
        qs = EmpresaInstituicao.objects.filter(cnpj=cnpj)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe uma empresa/instituição cadastrada com esse CNPJ.')
        return True

    def pode_desativar(self) -> bool:
        """A empresa só pode ser desativada se não estiver em uso."""
        if not self.object_instance.ativo:
            self.return_exception('A empresa/instituição já está inativa.')
        
        # Futuramente: checar vínculos com terceirizados
        return True

    def pode_reativar(self) -> bool:
        """A empresa só pode ser reativada se estiver inativa."""
        if self.object_instance.ativo:
            self.return_exception('A empresa/instituição já está ativa.')
        return True
