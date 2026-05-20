from AppCore.core.rules.rules import ModelInstanceRules


class SetorRules(ModelInstanceRules):

    def sigla_unica(self, sigla: str, excluir_id=None) -> bool:
        """Valida que a sigla não está em uso por outro setor."""
        from .models import Setor
        qs = Setor.objects.filter(sigla=sigla)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe um setor cadastrado com essa sigla.')
        return True

    def pode_desativar(self) -> bool:
        """Setor só pode ser desativado se não possuir vínculos."""
        if not self.object_instance.ativo:
            self.return_exception('O setor já está inativo.')
        if self.object_instance.vinculos.exists():
            self.return_exception('Não é possível desativar um setor com vínculos ativos.')
        return True

    def pode_reativar(self) -> bool:
        """Setor só pode ser reativado se estiver inativo."""
        if self.object_instance.ativo:
            self.return_exception('O setor já está ativo.')
        return True


class FuncaoRules(ModelInstanceRules):

    def sigla_unica(self, sigla: str, excluir_id=None) -> bool:
        """Valida que a sigla não está em uso por outra função."""
        from .models import Funcao
        qs = Funcao.objects.filter(sigla=sigla)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        if qs.exists():
            self.return_exception('Já existe uma função cadastrada com essa sigla.')
        return True

    def pode_desativar(self) -> bool:
        """Função só pode ser desativada se não estiver em uso em nenhum vínculo."""
        if not self.object_instance.ativo:
            self.return_exception('A função já está inativa.')
        if self.object_instance.vinculos.exists():
            self.return_exception('Não é possível desativar uma função que está em uso.')
        return True

    def pode_reativar(self) -> bool:
        """Função só pode ser reativada se estiver inativa."""
        if self.object_instance.ativo:
            self.return_exception('A função já está ativa.')
        return True


class SetorVinculoRules(ModelInstanceRules):
    # TODO (PessoasInstitucionais — Etapa 3): implementar regra
    # 'responsavel deve ser Servidor' quando o domínio PessoasInstitucionais existir.

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
