from django.db.models import Count, Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from Transporte.strikes.choices import StatusStrike


class JustificativaHelpers(ModelInstanceHelpers):

    def listar_com_relacionamentos(self):
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

    def pertence_ao_usuario(self, usuario):
        return self.object_instance.strike.ticket.aluno.usuario == usuario
