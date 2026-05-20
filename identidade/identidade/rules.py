import re

from AppCore.core.rules.rules import ModelInstanceRules


class UsuarioRules(ModelInstanceRules):
    """
    Regras de negócio do domínio Identidade.
    Valida pré-condições para operações sobre Usuario e entidades do UsuarioAggregate.
    Chamada exclusivamente pela camada Business.
    """

    # ------------------------------------------------------------------
    # Regras de formato e unicidade (não dependem de object_instance)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Regras de estado (dependem de self.object_instance)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Regras sobre Matricula (dependem de self.object_instance)
    # ------------------------------------------------------------------

    def matricula_nao_duplicada(self, numero_matricula: str, excluir_id=None) -> bool:
        """Valida que o número de matrícula não está duplicado para o mesmo usuário."""
        from .models import Matricula
        qs = Matricula.objects.filter(
            usuario=self.object_instance,
            matricula=numero_matricula,
        )
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('O usuário já possui essa matrícula registrada.')
        return True
