import logging

from django.utils import timezone

from Academico.alunos.models import Aluno
from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket

logger = logging.getLogger(__name__)


class EntradaSemTicketBusiness(ModelInstanceBusiness):

    def registrar(self, execucao_id, cpf, observacao=''):
        try:
            from .models import EntradaSemTicket

            execucao = ExecucaoRota.objects.select_for_update().select_related(
                'rota',
                'rota__percurso',
            ).get(pk=execucao_id)
            rules = self.object_instance.rules
            rules.validar_execucao_em_embarque(execucao)
            rules.validar_chamada_concluida(execucao)

            cpf_limpo = ''.join(ch for ch in str(cpf) if ch.isdigit()) or str(cpf).strip()
            aluno = Aluno().helper.obter_por_cpf(cpf_limpo)
            if aluno is None and cpf_limpo != str(cpf).strip():
                aluno = Aluno().helper.obter_por_cpf(str(cpf).strip())
            if aluno is None:
                raise NotFoundException('Aluno não encontrado para o CPF informado.')

            ticket = self.object_instance.helper.obter_ticket_ativo(execucao, aluno)
            rules.validar_aluno_sem_ticket_ativo(ticket)
            if ticket is not None and ticket.status == StatusTicket.EM_ESPERA:
                ticket.embarcado_em = timezone.now()
                ticket.state.atualizar_status(StatusTicket.EMBARCADO)
                return ticket, None

            rules.validar_entrada_inexistente(
                self.object_instance.helper.existe_para_aluno(execucao, aluno),
            )
            rules.validar_fila_de_espera_vazia(
                execucao.tickets.filter(status=StatusTicket.EM_ESPERA).count(),
            )
            resumo = execucao.business.obter_resumo_vagas()
            rules.validar_vaga_disponivel(resumo['vagas_disponiveis'])

            entrada = EntradaSemTicket.objects.create(
                execucao_rota=execucao,
                aluno=aluno,
                cpf=aluno.usuario.cpf,
                observacao=observacao or '',
                data_hora_entrada=timezone.now(),
            )
            return None, entrada
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível registrar a entrada sem ticket.',
                logger,
            )
