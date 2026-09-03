from django.db.models import Exists, OuterRef, Prefetch, Q

from Academico.aluno_cursos.models import AlunoCurso
from Transporte.justificativas.choices import StatusJustificativa
from Transporte.justificativas.models import Justificativa
from Transporte.strikes.models import Strike
from Transporte.tickets.models import Ticket


class BloqueioHelpers:

    def _queryset_com_relacionamentos(self):
        from Academico.alunos.models import Aluno

        strikes_prefetch = Prefetch(
            'tickets_transporte',
            queryset=Ticket.objects.select_related(
                'strike',
                'execucao_rota',
                'execucao_rota__rota',
                'execucao_rota__rota__percurso',
            ).filter(strike__isnull=False),
        )
        vinculos_cursos_prefetch = Prefetch(
            'vinculos_cursos',
            queryset=AlunoCurso.objects.filter(ativo=True)
            .select_related('curso')
            .order_by('id'),
            to_attr='vinculos_cursos_ativos',
        )
        justificativas_prefetch = Prefetch(
            'justificativas_transporte',
            queryset=Justificativa.objects.filter(
                status=StatusJustificativa.PENDENTE,
            ).prefetch_related(
                Prefetch(
                    'strikes_cobertos',
                    queryset=Strike.objects.select_related(
                        'ticket',
                        'ticket__execucao_rota',
                    ),
                ),
            ),
            to_attr='justificativas_pendentes',
        )
        return Aluno.objects.filter(is_bloqueado=True).select_related(
            'usuario',
        ).prefetch_related(
            strikes_prefetch,
            vinculos_cursos_prefetch,
            justificativas_prefetch,
        ).order_by('-faltas', 'usuario__nome')

    def _aplicar_filtros(self, qs, busca=None, curso_id=None, tem_justificativa=None):
        if busca:
            busca_limpa = busca.strip()
            cpf_busca = ''.join(ch for ch in busca_limpa if ch.isdigit())
            filtro_busca = Q(usuario__nome__unaccent__icontains=busca_limpa)
            if cpf_busca:
                filtro_busca |= Q(usuario__cpf__icontains=cpf_busca)
            qs = qs.filter(filtro_busca)

        if curso_id and str(curso_id).isdigit():
            qs = qs.filter(
                vinculos_cursos__curso_id=int(curso_id),
                vinculos_cursos__ativo=True,
            ).distinct()

        if tem_justificativa is not None:
            tem_justificativa_bool = str(tem_justificativa).lower() == 'true'
            justificativa_pendente = Justificativa.objects.filter(
                aluno_id=OuterRef('pk'),
                status=StatusJustificativa.PENDENTE,
            )
            if tem_justificativa_bool:
                qs = qs.filter(Exists(justificativa_pendente))
            else:
                qs = qs.exclude(Exists(justificativa_pendente))

        return qs

    def listar_bloqueados(self, busca=None, curso_id=None, tem_justificativa=None):
        qs = self._queryset_com_relacionamentos()
        return self._aplicar_filtros(qs, busca=busca, curso_id=curso_id, tem_justificativa=tem_justificativa)

    def obter_detalhe(self, aluno_pk):
        return self._queryset_com_relacionamentos().get(pk=aluno_pk)
