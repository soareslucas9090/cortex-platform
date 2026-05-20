import re

from AppCore.core.rules.rules import ModelInstanceRules


class UsuarioRules(ModelInstanceRules):
    """
    Regras de negócio do domínio Usuários.
    Valida pré-condições para operações sobre o model Usuario.
    Chamada exclusivamente pela camada Business.
    """

    def cpf_formato_valido(self, cpf: str) -> bool:
        """Valida que o CPF contém exatamente 11 dígitos numéricos."""
        cpf_limpo = re.sub(r'\D', '', cpf)
        if len(cpf_limpo) != 11:
            self.return_exception('O CPF deve conter exatamente 11 dígitos.')
        return True

    def cpf_unico(self, cpf: str, excluir_id=None) -> bool:
        """Valida que o CPF não está em uso por outro usuário."""
        from .models import Usuario
        qs = Usuario.objects.filter(cpf=cpf)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um usuário cadastrado com esse CPF.')
        return True

    def pode_desativar(self) -> bool:
        """Verifica se o usuário pode ser desativado."""
        if not self.object_instance.ativo:
            self.return_exception('O usuário já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Verifica se o usuário pode ser reativado."""
        if self.object_instance.ativo:
            self.return_exception('O usuário já está ativo.')
        return True
