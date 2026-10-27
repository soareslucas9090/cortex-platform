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

    def obter_por_sigla_normalizada(self, sigla):
        """Retorna o setor cuja sigla coincide após normalização de texto, ou None."""
        from AppCore.common.util.util import normalizar_chave_texto
        from .models import Setor

        chave = normalizar_chave_texto(sigla)
        if not chave:
            return None
        for setor in Setor.objects.all():
            if normalizar_chave_texto(setor.sigla) == chave:
                return setor
        return None
