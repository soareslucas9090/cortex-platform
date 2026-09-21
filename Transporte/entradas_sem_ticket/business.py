import logging

from django.utils import timezone

from AppCore.common.util.util import normalizar_cpf
from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException, NotFoundException
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.tickets.choices import StatusTicket
from Transporte.tickets.models import Ticket

logger = logging.getLogger(__name__)


class EntradaSemTicketBusiness(ModelInstanceBusiness):

    def _resolver_aluno_por_cpf(self, cpf):
        try:
            self.object_instance.rules.validar_cpf_informado(cpf)
            cpf_limpo = normalizar_cpf(str(cpf))
            self.object_instance.rules.validar_cpf_com_onze_digitos(cpf_limpo)
            aluno = self.object_instance.helper.obter_aluno_por_cpf(cpf_limpo)
            if aluno is None:
                raise NotFoundException('Aluno não encontrado para o CPF informado.')
            return aluno, cpf_limpo
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível localizar o aluno pelo CPF.',
                logger,
            )

    def _validar_elegibilidade_cpf(self, execucao, aluno, bloquear_ticket=False):
        try:
            rules = self.object_instance.rules
            execucao.rules.validar_fase_cpf(execucao)
            self.object_instance.rules.validar_fase_cpf_aberta(execucao)

            Ticket().business.validar_aluno_para_entrada_cpf(aluno.usuario)

            ticket = self.object_instance.helper.obter_ticket_ativo(
                execucao,
                aluno,
                bloquear=bloquear_ticket,
            )
            if ticket is not None and ticket.status == StatusTicket.EMBARCADO:
                return ticket, None
            entrada_existente = self.object_instance.helper.obter_entrada_por_aluno(
                execucao,
                aluno,
            )
            if entrada_existente is not None:
                return ticket, entrada_existente
            if ticket is not None and ticket.status not in (
                StatusTicket.AUSENTE,
                StatusTicket.EM_ESPERA,
            ):
                rules.validar_aluno_sem_ticket_ativo(ticket)
            if ticket is None:
                rules.validar_entrada_inexistente(False)
            return ticket, None
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível validar a elegibilidade da entrada sem ticket.',
                logger,
            )

    def validar_elegibilidade(self, execucao_id, cpf):
        try:
            execucao = ExecucaoRota().business.obter_para_conferencia(
                execucao_id,
                exigir_embarque=True,
            )
            aluno, _cpf = self._resolver_aluno_por_cpf(cpf)
            self._validar_elegibilidade_cpf(execucao, aluno)
            return aluno
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível validar a entrada sem ticket.',
                logger,
            )

    def registrar_um(self, execucao_id, cpf):
        try:
            from .models import EntradaSemTicket

            execucao = ExecucaoRota().business.obter_para_conferencia(
                execucao_id,
                exigir_embarque=True,
                bloquear=True,
            )
            aluno, cpf_limpo = self._resolver_aluno_por_cpf(cpf)
            ticket, entrada_existente = self._validar_elegibilidade_cpf(
                execucao,
                aluno,
                bloquear_ticket=True,
            )
            if entrada_existente is not None:
                return {
                    'entrada': entrada_existente,
                    'ticket': ticket,
                    'replay': True,
                }
            if ticket is not None and ticket.status == StatusTicket.EMBARCADO:
                return {
                    'entrada': None,
                    'ticket': ticket,
                    'replay': True,
                }

            agora = timezone.now()
            entrada = None
            if ticket is not None and ticket.status == StatusTicket.AUSENTE:
                ticket.embarcado_em = agora
                ticket.state.atualizar_status(StatusTicket.EMBARCADO)
            elif ticket is not None and ticket.status == StatusTicket.EM_ESPERA:
                ticket.business.marcar_contemplado()
                entrada = EntradaSemTicket.objects.create(
                    execucao_rota=execucao,
                    aluno=aluno,
                    cpf=cpf_limpo,
                    observacao='',
                    data_hora_entrada=agora,
                )
            else:
                entrada = EntradaSemTicket.objects.create(
                    execucao_rota=execucao,
                    aluno=aluno,
                    cpf=cpf_limpo,
                    observacao='',
                    data_hora_entrada=agora,
                )
            return {
                'entrada': entrada,
                'ticket': ticket,
                'replay': False,
            }
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível registrar a entrada sem ticket.',
                logger,
            )
