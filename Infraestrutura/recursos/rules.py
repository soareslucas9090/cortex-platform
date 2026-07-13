from AppCore.core.rules.rules import ModelInstanceRules

from .choices import TipoRecurso


class RecursoRules(ModelInstanceRules):

    def codigo_unico(self, codigo: str, excluir_id=None) -> bool:
        """Valida que o código de negócio não está em uso por outro recurso."""
        from .models import Recurso
        qs = Recurso.objects.filter(codigo__iexact=codigo)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um recurso cadastrado com esse código.')
        return True

    def validar_sala_por_tipo(self, tipo: str, sala_id=None) -> bool:
        """Chave exige sala; demais tipos aceitam sala opcional."""
        if tipo == TipoRecurso.CHAVE and not sala_id:
            self.return_exception('Recursos do tipo chave devem estar vinculados a uma sala.')
        return True

    def validar_sala_ativa(self, sala_id=None) -> bool:
        """Sala informada deve existir e estar ativa."""
        if sala_id is None:
            return True
        from salas.models import Sala
        sala = Sala.objects.filter(pk=sala_id).first()
        if sala is None:
            self.return_exception('Sala informada não encontrada.')
        if not sala.ativo:
            self.return_exception('A sala informada está inativa.')
        return True

    def pode_desativar(self) -> bool:
        """Recurso só pode ser desativado se estiver ativo."""
        if not self.object_instance.ativo:
            self.return_exception('O recurso já está inativo.')
        return True

    def pode_reativar(self) -> bool:
        """Recurso só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O recurso já está ativo.')
        return True
