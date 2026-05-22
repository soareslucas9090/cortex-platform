from AppCore.core.rules.rules import ModelInstanceRules


class SetorVinculoRules(ModelInstanceRules):
    def usuario_e_servidor(self, usuario) -> bool:
        """Valida se o usuário informado possui perfil de servidor ativo."""
        if not hasattr(usuario, 'servidor') or not usuario.servidor.ativo:
            self.return_exception('Apenas servidores ativos podem ocupar a responsabilidade principal de um setor.')
        return True
    def setor_esta_ativo(self, setor) -> bool:
        """Vínculo só pode ser criado em setor ativo."""
        if not setor.ativo:
            self.return_exception('Não é possível vincular usuário a um setor inativo.')
        return True

    def funcao_esta_ativa(self, funcao) -> bool:
        """Vínculo só pode ser criado com função ativa."""
        if not funcao.ativo:
            self.return_exception('Não é possível criar vínculo com função inativa.')
        return True

    def vinculo_sem_duplicata(self, usuario, setor, funcao, excluir_id=None) -> bool:
        """Valida que não existe um vínculo idêntico (mesmo usuario+setor+funcao)."""
        from .models import SetorVinculo
        qs = SetorVinculo.objects.filter(usuario=usuario, setor=setor, funcao=funcao)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um vínculo com essa combinação de usuário, setor e função.')
        return True

    def setor_mantem_responsavel(self, excluir_id=None) -> bool:
        """
        Valida que o setor mantém ao menos um responsável após a operação.
        excluir_id: pk do vínculo que será removido/atualizado, para excluí-lo da contagem.
        """
        setor = self.object_instance.setor
        qs = setor.vinculos.filter(responsavel=True)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if not qs.exists():
            self.return_exception('O setor deve manter ao menos um vínculo responsável.')
        return True
