from AppCore.core.helpers.helpers import ModelInstanceHelpers


class EntradaSemTicketHelpers(ModelInstanceHelpers):

    def contar_da_execucao(self, execucao):
        from .models import EntradaSemTicket

        return EntradaSemTicket.objects.filter(execucao_rota=execucao).count()

    def existe_para_aluno(self, execucao, aluno) -> bool:
        from .models import EntradaSemTicket

        return EntradaSemTicket.objects.filter(
            execucao_rota=execucao,
            aluno=aluno,
        ).exists()

    def listar_por_cpfs(self, execucao, cpfs):
        from .models import EntradaSemTicket

        return list(
            EntradaSemTicket.objects.filter(
                execucao_rota=execucao,
                cpf__in=cpfs,
            ).select_related('aluno', 'aluno__usuario').order_by('data_hora_entrada')
        )

    def obter_aluno_por_cpf(self, cpf_limpo):
        from Academico.alunos.models import Aluno

        return Aluno.objects.select_related('usuario').filter(
            usuario__cpf=cpf_limpo,
        ).first()

    def obter_ticket_ativo(self, execucao, aluno, bloquear=False):
        from Transporte.tickets.choices import StatusTicket
        from Transporte.tickets.models import Ticket

        queryset = Ticket.objects.filter(
            execucao_rota=execucao,
            aluno=aluno,
        ).exclude(status=StatusTicket.CANCELADO).select_related('execucao_rota')
        if bloquear:
            queryset = queryset.select_for_update()
        return queryset.first()
