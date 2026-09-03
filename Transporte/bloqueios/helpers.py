from django.db.models import Prefetch

from Transporte.justificativas.choices import StatusJustificativa
from Transporte.justificativas.models import Justificativa
from Transporte.strikes.models import Strike


class BloqueioHelpers:

    def _queryset_com_relacionamentos(self):
        from Academico.alunos.models import Aluno

        strikes_prefetch = Prefetch(
            'tickets_transporte__strike',
            queryset=Strike.objects.select_related(
                'ticket',
                'ticket__execucao_rota',
                'ticket__execucao_rota__rota',
                'ticket__execucao_rota__rota__percurso',
            ),
        )
        justificativas_prefetch = Prefetch(
            'justificativas_transporte',
            queryset=Justificativa.objects.filter(status=StatusJustificativa.PENDENTE),
            to_attr='justificativas_pendentes',
        )
        return Aluno.objects.filter(is_bloqueado=True).select_related(
            'usuario',
        ).prefetch_related(
            strikes_prefetch,
            justificativas_prefetch,
        ).order_by('-faltas', 'usuario__nome')

    def listar_bloqueados(self):
        return self._queryset_com_relacionamentos()

    def obter_detalhe(self, aluno_pk):
        return self._queryset_com_relacionamentos().get(pk=aluno_pk)
