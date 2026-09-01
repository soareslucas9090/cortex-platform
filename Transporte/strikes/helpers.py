from django.db.models import Count, Q

from AppCore.core.helpers.helpers import ModelInstanceHelpers

from .choices import StatusStrike


class StrikeHelpers(ModelInstanceHelpers):

    def listar_com_relacionamentos(self):
        from .models import Strike

        return Strike.objects.select_related(
            'ticket',
            'ticket__execucao_rota',
            'ticket__execucao_rota__rota',
            'ticket__execucao_rota__rota__percurso',
            'ticket__aluno',
            'ticket__aluno__usuario',
        ).annotate(
            quantidade_strikes_ativos=Count(
                'ticket__aluno__tickets_transporte',
                filter=Q(
                    ticket__aluno__tickets_transporte__strike__status=StatusStrike.ATIVO,
                ),
                distinct=True,
            ),
        )

    def contar_ativos_do_aluno(self):
        from .models import Strike

        aluno_id = self.object_instance.ticket.aluno_id
        return Strike.objects.filter(
            ticket__aluno_id=aluno_id,
            status=StatusStrike.ATIVO,
        ).count()

    def aluno_esta_bloqueado(self):
        return self.contar_ativos_do_aluno() >= 3
