from AppCore.core.rules.rules import ModelInstanceRules


class CursoRules(ModelInstanceRules):

    def codigo_unico(self, codigo: str, excluir_id=None) -> bool:
        """Valida que o código do curso não está em uso."""
        from .models import Curso
        qs = Curso.objects.filter(codigo_curso__iexact=codigo)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um curso cadastrado com esse código.')
        return True

    def pode_desativar(self) -> bool:
        """Curso só pode ser desativado se já estiver ativo."""
        if not self.object_instance.ativo:
            self.return_exception('O curso já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Curso só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O curso já está ativo.')
        return True
