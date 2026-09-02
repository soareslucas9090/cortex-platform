import logging

from django.utils import timezone

from Academico.alunos.models import Aluno
from AppCore.common.util.util import normalizar_cpf
from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException
from Transporte.execucoes_rotas.models import ExecucaoRota
from Transporte.tickets.models import Ticket

logger = logging.getLogger(__name__)


class EntradaSemTicketBusiness(ModelInstanceBusiness):

    def _resolver_aluno_por_cpf(self, cpf):
        try:
            self.object_instance.rules.validar_cpf_informado(cpf)
            cpf_limpo = normalizar_cpf(str(cpf))
            if len(cpf_limpo) != 11:
                raise NotFoundException('Aluno não encontrado para o CPF informado.')
            aluno = Aluno().helper.obter_por_cpf(cpf_limpo)
            if aluno is None:
                raise NotFoundException('Aluno não encontrado para o CPF informado.')
            return aluno, cpf_limpo
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível localizar o aluno pelo CPF.',
                logger,
            )

    def _aplicar_regras_elegibilidade(self, execucao, aluno):
        try:
            rules = self.object_instance.rules
            rules.validar_execucao_em_embarque(execucao)
            rules.validar_chamada_concluida(execucao)

            strikes = Ticket().helper.contar_strikes_ativos(aluno)
            Ticket().rules.validar_aluno_elegivel(aluno.usuario, strikes)

            ticket = self.object_instance.helper.obter_ticket_ativo(execucao, aluno)
            rules.validar_aluno_sem_ticket_ativo(ticket)
            rules.validar_entrada_inexistente(
                self.object_instance.helper.existe_para_aluno(execucao, aluno),
            )
            rules.validar_fila_de_espera_vazia(Ticket().helper.contar_espera(execucao))
            resumo = execucao.business.obter_resumo_vagas()
            rules.validar_vaga_disponivel(resumo['vagas_disponiveis'])
            return aluno
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
            self._aplicar_regras_elegibilidade(execucao, aluno)
            return aluno
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível validar a entrada sem ticket.',
                logger,
            )

    def registrar(self, execucao_id, cpf, observacao=''):
        try:
            from .models import EntradaSemTicket

            execucao = ExecucaoRota().business.obter_para_conferencia(
                execucao_id,
                exigir_embarque=True,
            )
            execucao = ExecucaoRota().helper.obter_por_id(execucao.pk, bloquear=True)
            aluno, cpf_limpo = self._resolver_aluno_por_cpf(cpf)
            self._aplicar_regras_elegibilidade(execucao, aluno)

            entrada = EntradaSemTicket.objects.create(
                execucao_rota=execucao,
                aluno=aluno,
                cpf=cpf_limpo,
                observacao=observacao or '',
                data_hora_entrada=timezone.now(),
            )
            return entrada
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível registrar a entrada sem ticket.',
                logger,
            )
