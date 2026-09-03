from datetime import date, time

from django.db.models import Count, Max, Min, Q

from Academico.aluno_cursos.models import AlunoCurso
from Academico.alunos.models import Aluno
from Identidade.matriculas.choices import SituacaoMatricula
from Identidade.matriculas.models import Matricula
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.strikes.choices import StatusStrike
from Transporte.strikes.models import Strike
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket


class RelatorioAlunosHelpers:

    def obter_tickets_no_periodo(self, data_inicio: date, data_fim: date):
        return Ticket.objects.filter(
            execucao_rota__data_execucao__gte=data_inicio,
            execucao_rota__data_execucao__lte=data_fim,
        ).select_related(
            'execucao_rota__rota',
            'aluno__usuario',
        )

    def obter_execucoes_no_periodo(self, data_inicio: date, data_fim: date):
        return ExecucaoRota.objects.filter(
            data_execucao__gte=data_inicio,
            data_execucao__lte=data_fim,
        ).select_related('rota')

    def obter_ids_alunos_bloqueados(self):
        return set(
            Strike.objects.filter(status=StatusStrike.ATIVO)
            .values('ticket__aluno_id')
            .annotate(total=Count('id'))
            .filter(total__gte=3)
            .values_list('ticket__aluno_id', flat=True),
        )

    def aluno_esta_bloqueado(self, aluno_id: int) -> bool:
        total = Strike.objects.filter(
            ticket__aluno_id=aluno_id,
            status=StatusStrike.ATIVO,
        ).count()
        return total >= 3

    def contar_strikes_ativos(self, aluno_id: int) -> int:
        return Strike.objects.filter(
            ticket__aluno_id=aluno_id,
            status=StatusStrike.ATIVO,
        ).count()

    def obter_ids_alunos_com_ticket_no_periodo(self, data_inicio: date, data_fim: date):
        return set(
            self.obter_tickets_no_periodo(data_inicio, data_fim)
            .exclude(status=StatusTicket.CANCELADO)
            .values_list('aluno_id', flat=True)
            .distinct(),
        )

    def obter_alunos_sem_ticket_no_periodo(self, data_inicio: date, data_fim: date):
        com_ticket = self.obter_ids_alunos_com_ticket_no_periodo(data_inicio, data_fim)
        return Aluno.objects.filter(ativo=True).exclude(
            usuario_id__in=com_ticket,
        ).select_related('usuario')

    def formatar_horario(self, horario: time) -> str:
        return horario.strftime('%H:%M')

    def obter_horarios_do_periodo(self, data_inicio: date, data_fim: date):
        horarios = (
            self.obter_execucoes_no_periodo(data_inicio, data_fim)
            .values_list('rota__horario_saida', flat=True)
            .distinct()
        )
        return sorted({self.formatar_horario(h) for h in horarios if h is not None})

    def montar_resumo_por_horario(
        self,
        tickets,
        bloqueados_ids: set[int],
        data_inicio: date,
        data_fim: date,
    ):
        horarios = self.obter_horarios_do_periodo(data_inicio, data_fim)
        resultado = []

        for horario_str in horarios:
            tickets_horario = tickets.filter(
                execucao_rota__rota__horario_saida__hour=int(horario_str.split(':')[0]),
                execucao_rota__rota__horario_saida__minute=int(horario_str.split(':')[1]),
            )
            execucoes_horario = self.obter_execucoes_no_periodo(data_inicio, data_fim).filter(
                rota__horario_saida__hour=int(horario_str.split(':')[0]),
                rota__horario_saida__minute=int(horario_str.split(':')[1]),
            )
            execucao_ids = set(execucoes_horario.values_list('id', flat=True))
            alunos_com_ticket_horario = set(
                tickets_horario.exclude(status=StatusTicket.CANCELADO)
                .values_list('aluno_id', flat=True)
                .distinct(),
            )
            alunos_ativos_total = Aluno.objects.filter(ativo=True).count()
            sem_ticket = max(
                0,
                alunos_ativos_total - len(alunos_com_ticket_horario),
            ) if execucao_ids else 0

            resultado.append({
                'horario': horario_str,
                'presentes': tickets_horario.filter(status=StatusTicket.EMBARCADO).count(),
                'ausentes': tickets_horario.filter(status=StatusTicket.AUSENTE).count(),
                'em_espera': tickets_horario.filter(status=StatusTicket.EM_ESPERA).count(),
                'bloqueados': tickets_horario.filter(
                    aluno_id__in=bloqueados_ids,
                ).values('aluno_id').distinct().count(),
                'sem_ticket': sem_ticket,
            })

        return resultado

    def enriquecer_aluno(self, aluno: Aluno, data_inicio: date, data_fim: date, categoria: str):
        usuario = aluno.usuario
        turma = (
            AlunoCurso.objects.filter(aluno=aluno, ativo=True)
            .select_related('curso')
            .order_by('-created_at')
            .values_list('curso__nome', flat=True)
            .first()
        )
        matricula = (
            Matricula.objects.filter(
                usuario_id=usuario.pk,
                situacao=SituacaoMatricula.ATIVA,
            )
            .values_list('matricula', flat=True)
            .first()
        )
        tickets_aluno = Ticket.objects.filter(aluno=aluno)
        tickets_periodo = tickets_aluno.filter(
            execucao_rota__data_execucao__gte=data_inicio,
            execucao_rota__data_execucao__lte=data_fim,
        )
        embarques = tickets_aluno.filter(
            status=StatusTicket.EMBARCADO,
            embarcado_em__isnull=False,
        ).aggregate(
            primeiro=Min('embarcado_em'),
            ultimo=Max('embarcado_em'),
        )
        ausencias = tickets_periodo.filter(status=StatusTicket.AUSENTE).count()
        bloqueios = self.contar_strikes_ativos(aluno.pk)
        bloqueado = bloqueios >= 3

        if bloqueado:
            status_label = 'Bloqueado'
        elif categoria == 'presentes':
            status_label = 'Presente'
        elif categoria == 'ausencias':
            status_label = 'Ausente'
        elif categoria == 'sem_ticket':
            status_label = 'Sem ticket'
        else:
            status_label = 'Ativo'

        primeiro_uso = embarques['primeiro'].date() if embarques['primeiro'] else None
        ultimo_uso = embarques['ultimo'].date() if embarques['ultimo'] else None

        return {
            'usuario_id': usuario.pk,
            'nome': usuario.nome,
            'foto': usuario.foto,
            'turma': turma,
            'matricula': matricula,
            'turno': None,
            'pcd': bool(usuario.deficiencia),
            'primeiro_uso': primeiro_uso,
            'ultimo_uso': ultimo_uso,
            'ausencias': ausencias,
            'bloqueios': bloqueios,
            'status': status_label,
        }
