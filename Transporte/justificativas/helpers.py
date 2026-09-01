from django.db.models import Count, Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from Transporte.strikes.choices import StatusStrike


class JustificativaHelpers(ModelInstanceHelpers):

    def _listar_com_relacionamentos(self):
        from .models import Justificativa

        return Justificativa.objects.select_related(
            'strike',
            'strike__ticket',
            'strike__ticket__execucao_rota',
            'strike__ticket__execucao_rota__rota',
            'strike__ticket__execucao_rota__rota__percurso',
            'strike__ticket__aluno',
            'strike__ticket__aluno__usuario',
            'analisada_por',
        ).annotate(
            quantidade_strikes_ativos=Count(
                'strike__ticket__aluno__tickets_transporte',
                filter=Q(
                    strike__ticket__aluno__tickets_transporte__strike__status=StatusStrike.ATIVO,
                ),
                distinct=True,
            ),
        )

    def listar_para_usuario(self, usuario):
        queryset = self._listar_com_relacionamentos()
        if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
            return queryset
        aluno = getattr(usuario, 'aluno', None)
        return (
            queryset.filter(strike__ticket__aluno=aluno)
            if aluno is not None
            else queryset.none()
        )

    def obter_por_id(self, justificativa_id):
        return self._listar_com_relacionamentos().get(pk=justificativa_id)
