from AppCore.core.rules.rules import ModelInstanceRules
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.tickets.choices import StatusTicket

MENSAGEM_VAGA_RESERVADA_ESPERA = 'As vagas restantes estão reservadas à fila de espera.'


class EntradaSemTicketRules(ModelInstanceRules):

    def validar_cpf_informado(self, cpf) -> bool:
        if not cpf or not str(cpf).strip():
            self.return_exception('Informe o CPF do aluno.')
        return True

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

    def validar_vaga_alem_da_espera(self, vagas_disponiveis, quantidade_espera) -> bool:
        if vagas_disponiveis <= quantidade_espera:
            self.return_exception(MENSAGEM_VAGA_RESERVADA_ESPERA)
        return True

    def validar_vaga_disponivel(self, vagas_disponiveis) -> bool:
        if vagas_disponiveis < 1:
            self.return_exception('Não há vagas disponíveis para entrada sem ticket.')
        return True

    def validar_aluno_sem_ticket_ativo(self, ticket) -> bool:
        if ticket is None or ticket.status == StatusTicket.AUSENTE:
            return True
        if ticket.status == StatusTicket.EM_ESPERA:
            self.return_exception(
                'Aluno em espera deve ser tratado na fila, não pelo fluxo sem ticket.'
            )
        self.return_exception('O aluno já possui ticket ou entrada nesta execução.')

    def validar_entrada_inexistente(self, existe_entrada) -> bool:
        if existe_entrada:
            self.return_exception('O aluno já possui ticket ou entrada nesta execução.')
        return True
