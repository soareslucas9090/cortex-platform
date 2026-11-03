from AppCore.core.rules.rules import ModelInstanceRules


class TipoAutorizacaoAcessoRules(ModelInstanceRules):

    def validar_nome_unico(self, nome: str, excluir_id=None) -> bool:
        from .models import TipoAutorizacaoAcesso

        if not (nome or '').strip():
            self.return_exception('O nome do tipo de autorização é obrigatório.')
        qs = TipoAutorizacaoAcesso.objects.filter(nome__iexact=nome.strip())
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um tipo de autorização cadastrado com esse nome.')
        return True

    def validar_nome_tipo_base(self, nome: str) -> bool:
        if self.object_instance.eh_base and nome.strip() != self.object_instance.nome:
            self.return_exception('Não é possível alterar o nome de um tipo-base.')
        return True

    def pode_desativar(self) -> bool:
        if self.object_instance.eh_base:
            self.return_exception('Não é possível desativar um tipo-base.')
        if not self.object_instance.ativo:
            self.return_exception('O tipo de autorização já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        if self.object_instance.ativo:
            self.return_exception('O tipo de autorização já está ativo.')
        return True
