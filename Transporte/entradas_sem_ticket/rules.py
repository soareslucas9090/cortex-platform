from AppCore.core.rules.rules import ModelInstanceRules
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.tickets.choices import StatusTicket


class EntradaSemTicketRules(ModelInstanceRules):

    def validar_execucao_em_embarque(self, execucao) -> bool:
        if execucao.status != StatusExecucaoRota.EM_EMBARQUE:
            self.return_exception('A entrada sem ticket só é permitida durante o embarque.')
        return True

    def validar_chamada_concluida(self, execucao) -> bool:
        if not execucao.chamada_tickets_concluida:
            self.return_exception(
                'Finalize a chamada dos tickets antes de registrar entrada sem ticket.'
            )
        return True

    def validar_fila_de_espera_vazia(self, quantidade_espera) -> bool:
        if quantidade_espera > 0:
            self.return_exception(
                'Ainda há alunos na fila de espera. Não é possível incluir por CPF.'
            )
        return True

    def validar_vaga_disponivel(self, vagas_disponiveis) -> bool:
        if vagas_disponiveis < 1:
            self.return_exception('Não há vagas disponíveis para entrada sem ticket.')
        return True

    def validar_aluno_sem_ticket_ativo(self, ticket) -> bool:
        if ticket is None:
            return True
        if ticket.status == StatusTicket.EM_ESPERA:
            return True
        self.return_exception('O aluno já possui ticket ou entrada nesta execução.')
        return True

    def validar_entrada_inexistente(self, existe_entrada) -> bool:
        if existe_entrada:
            self.return_exception('O aluno já possui ticket ou entrada nesta execução.')
        return True
