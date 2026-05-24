from AppCore.core.rules.rules import ModelInstanceRules


class ServidorRules(ModelInstanceRules):

    def usuario_sem_perfil_servidor(self, usuario_pk) -> bool:
        """Valida que o usuário ainda não possui perfil de servidor."""
        from .models import Servidor
        if Servidor.objects.filter(pk=usuario_pk).exists():
            self.return_exception('Este usuário já possui perfil de servidor.')
        return True

    def cargo_ativo(self, cargo) -> bool:
        """Valida que o cargo informado está ativo."""
        if not cargo.ativo:
            self.return_exception('Não é possível vincular um cargo inativo ao servidor.')
        return True

    def pode_desativar(self) -> bool:
        """
        Servidor só pode ser desativado se estiver ativo e se não
        for responsável por nenhum setor ativo.

        Invariante organizacional: todo setor ativo deve manter ao menos
        um responsável ativo. Desativar um servidor que cumpre esse papel
        sem antes redistribuir a responsabilidade violaria essa regra.
        """
        if not self.object_instance.ativo:
            self.return_exception('O servidor já está inativo.')

        from Organizacional.vinculos.models import SetorVinculo
        vinculo_responsavel = SetorVinculo.objects.filter(
            usuario=self.object_instance.usuario,
            responsavel=True,
            setor__ativo=True,
        ).first()
        if vinculo_responsavel is not None:
            self.return_exception(
                f'O servidor é responsável pelo setor "{vinculo_responsavel.setor}". '
                'Transfira ou remova a responsabilidade antes de desativar o perfil de servidor.'
            )
        return True

    def pode_reativar(self) -> bool:
        """Servidor só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O servidor já está ativo.')
        return True
