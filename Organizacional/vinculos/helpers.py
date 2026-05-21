from AppCore.core.helpers.helpers import ModelInstanceHelpers


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
