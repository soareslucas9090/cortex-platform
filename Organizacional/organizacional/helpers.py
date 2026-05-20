from AppCore.core.helpers.helpers import ModelInstanceHelpers


class SetorHelpers(ModelInstanceHelpers):

    # ------------------------------------------------------------------
    # Consultas de instância (operam sobre self.object_instance = Setor)
    # ------------------------------------------------------------------

    def obter_vinculos(self):
        """Retorna todos os vínculos do setor."""
        return self.object_instance.vinculos.all()

    def obter_responsaveis(self):
        """Retorna os vínculos marcados como responsável no setor."""
        return self.object_instance.vinculos.filter(responsavel=True)

    def tem_responsavel(self) -> bool:
        """Verifica se o setor possui ao menos um responsável."""
        return self.object_instance.vinculos.filter(responsavel=True).exists()

    # ------------------------------------------------------------------
    # Consultas globais do domínio
    # ------------------------------------------------------------------

    def listar_ativos(self):
        """Retorna todos os setores ativos."""
        from .models import Setor
        return Setor.objects.filter(ativo=True)

    def listar_inativos(self):
        """Retorna todos os setores inativos."""
        from .models import Setor
        return Setor.objects.filter(ativo=False)


class FuncaoHelpers(ModelInstanceHelpers):

    # ------------------------------------------------------------------
    # Consultas de instância (operam sobre self.object_instance = Funcao)
    # ------------------------------------------------------------------

    def esta_em_uso(self) -> bool:
        """Verifica se a função está associada a algum vínculo."""
        return self.object_instance.vinculos.exists()

    def obter_vinculos(self):
        """Retorna todos os vínculos que utilizam esta função."""
        return self.object_instance.vinculos.all()

    # ------------------------------------------------------------------
    # Consultas globais do domínio
    # ------------------------------------------------------------------

    def listar_ativas(self):
        """Retorna todas as funções ativas."""
        from .models import Funcao
        return Funcao.objects.filter(ativo=True)

    def listar_inativas(self):
        """Retorna todas as funções inativas."""
        from .models import Funcao
        return Funcao.objects.filter(ativo=False)


class SetorVinculoHelpers(ModelInstanceHelpers):

    # ------------------------------------------------------------------
    # Consultas globais do domínio
    # ------------------------------------------------------------------

    def listar_por_usuario(self, usuario):
        """Retorna todos os vínculos de um usuário."""
        from .models import SetorVinculo
        return SetorVinculo.objects.filter(usuario=usuario)

    def listar_por_setor(self, setor):
        """Retorna todos os vínculos de um setor."""
        from .models import SetorVinculo
        return SetorVinculo.objects.filter(setor=setor)

    def listar_responsaveis_do_setor(self, setor):
        """Retorna os vínculos responsáveis de um setor."""
        from .models import SetorVinculo
        return SetorVinculo.objects.filter(setor=setor, responsavel=True)

    def vinculo_duplicado_existe(self, usuario, setor, funcao, excluir_id=None) -> bool:
        """Verifica se já existe um vínculo idêntico (usuario+setor+funcao)."""
        from .models import SetorVinculo
        qs = SetorVinculo.objects.filter(usuario=usuario, setor=setor, funcao=funcao)
        if excluir_id is not None:
            qs = qs.exclude(pk=excluir_id)
        return qs.exists()
