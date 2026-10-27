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

    def validar_setor_obrigatorio(self, setor_id) -> bool:
        """Todo curso deve possuir um setor ativo associado."""
        from Organizacional.setores.models import Setor

        if setor_id is None:
            self.return_exception('O curso deve possuir um setor associado.')

        setor = Setor.objects.filter(pk=setor_id).first()
        if setor is None:
            self.return_exception('Setor associado ao curso não encontrado.')
        if not setor.ativo:
            self.return_exception('O setor associado ao curso deve estar ativo.')
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
