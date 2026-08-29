from AppCore.core.rules.rules import ModelInstanceRules

MENSAGEM_APELIDO_DUPLICADO = 'Já existe um percurso cadastrado com esse apelido.'


class PercursoRules(ModelInstanceRules):

    def validar_apelido_unico(self, apelido: str, excluir_id=None) -> bool:
        """Valida que o apelido do percurso não está em uso."""
        from .models import Percurso
        qs = Percurso.objects.filter(apelido__iexact=apelido)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception(MENSAGEM_APELIDO_DUPLICADO)
        return True

    def pode_desativar(self) -> bool:
        """Percurso só pode ser desativado se estiver ativo e sem rotas ativas."""
        if not self.object_instance.ativo:
            self.return_exception('O percurso já está inativo.')
        if self.object_instance.rotas.filter(ativo=True).exists():
            self.return_exception('Não é possível desativar um percurso com rotas ativas.')
        return True

    def pode_reativar(self) -> bool:
        """Percurso só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O percurso já está ativo.')
        return True
