from AppCore.core.helpers.helpers import ModelInstanceHelpers


class JustificativaHelpers(ModelInstanceHelpers):

    def _listar_com_relacionamentos(self):
        from .models import Justificativa

        return Justificativa.objects.select_related(
            'aluno',
            'aluno__usuario',
            'analisada_por',
        ).prefetch_related(
            'strikes_cobertos',
            'strikes_cobertos__ticket',
            'strikes_cobertos__ticket__execucao_rota',
            'strikes_cobertos__ticket__execucao_rota__rota',
            'strikes_cobertos__ticket__execucao_rota__rota__percurso',
        )

    def listar_para_usuario(self, usuario):
        queryset = self._listar_com_relacionamentos()
        if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
            return queryset
        aluno = getattr(usuario, 'aluno', None)
        return queryset.filter(aluno=aluno) if aluno is not None else queryset.none()

    def obter_por_id(self, justificativa_id):
        return self._listar_com_relacionamentos().get(pk=justificativa_id)
