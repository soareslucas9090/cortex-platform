from AppCore.core.exceptions.exceptions import NotFoundException
from AppCore.core.rules.rules import ModelInstanceRules
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.tickets.choices import StatusTicket


class EntradaSemTicketRules(ModelInstanceRules):

    def validar_cpf_informado(self, cpf) -> bool:
        if not cpf or not str(cpf).strip():
            self.return_exception('Informe o CPF do aluno.')
        return True

    def validar_cpf_com_onze_digitos(self, cpf_limpo) -> bool:
        if len(cpf_limpo) != 11:
            self.return_exception(
                'Aluno não encontrado para o CPF informado.',
                type_exception=NotFoundException,
            )
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

    def validar_lote_cpf_aberto(self, execucao) -> bool:
        if execucao.entradas_cpf_concluidas:
            self.return_exception(
                'A entrada por CPF desta execução já foi concluída.',
            )
        return True

    def validar_vaga_disponivel(self, vagas_disponiveis) -> bool:
        if vagas_disponiveis < 1:
            self.return_exception('Não há vagas disponíveis para entrada sem ticket.')
        return True

    def validar_cpfs_sem_duplicata(self, cpfs) -> bool:
        if len(cpfs) != len(set(cpfs)):
            self.return_exception('Há CPFs duplicados na lista.')
        return True

    def validar_lote_cabe_nas_vagas(self, quantidade, vagas_disponiveis) -> bool:
        if quantidade > vagas_disponiveis:
            self.return_exception(
                'Não há vagas suficientes para todos os CPFs informados.'
            )
        return True

    def validar_aluno_sem_ticket_ativo(self, ticket) -> bool:
        if ticket is None or ticket.status in (
            StatusTicket.AUSENTE,
            StatusTicket.EM_ESPERA,
        ):
            return True
        self.return_exception('O aluno já possui ticket ou entrada nesta execução.')

    def validar_entrada_inexistente(self, existe_entrada) -> bool:
        if existe_entrada:
            self.return_exception('O aluno já possui ticket ou entrada nesta execução.')
        return True

    def validar_replay_lote(self, cpfs, persistidos) -> bool:
        if set(cpfs) != set(persistidos):
            self.return_exception(
                'A entrada por CPF desta execução já foi concluída com outro conjunto.',
            )
        return True
