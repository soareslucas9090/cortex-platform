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

    def obter_ticket_ativo(self, execucao, aluno):
        from Transporte.tickets.choices import StatusTicket
        from Transporte.tickets.models import Ticket

        return Ticket.objects.filter(
            execucao_rota=execucao,
            aluno=aluno,
        ).exclude(status=StatusTicket.CANCELADO).first()
