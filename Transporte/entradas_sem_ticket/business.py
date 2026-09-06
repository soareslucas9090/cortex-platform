import logging

from django.utils import timezone

from AppCore.common.util.util import normalizar_cpf
from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import NotFoundException
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

    def _aplicar_regras_elegibilidade(self, execucao, aluno, bloquear_ticket=False):
        try:
            rules = self.object_instance.rules
            rules.validar_execucao_em_embarque(execucao)
            rules.validar_chamada_concluida(execucao)

            Ticket().business.validar_elegibilidade_aluno(aluno.usuario)

            ticket = self.object_instance.helper.obter_ticket_ativo(
                execucao,
                aluno,
                bloquear=bloquear_ticket,
            )
            rules.validar_aluno_sem_ticket_ativo(ticket)
            rules.validar_entrada_inexistente(
                self.object_instance.helper.existe_para_aluno(execucao, aluno),
            )
            resumo = execucao.business.obter_resumo_vagas()
            rules.validar_vaga_disponivel(resumo['vagas_disponiveis'])
            return ticket
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
            self.object_instance.rules.validar_lote_cpf_aberto(execucao)
            aluno, _cpf = self._resolver_aluno_por_cpf(cpf)
            self._aplicar_regras_elegibilidade(execucao, aluno)
            return aluno
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível validar a entrada sem ticket.',
                logger,
            )

    def registrar(self, execucao_id, cpfs):
        try:
            from .models import EntradaSemTicket

            execucao = ExecucaoRota().business.obter_para_conferencia(
                execucao_id,
                exigir_embarque=True,
                bloquear=True,
            )
            rules = self.object_instance.rules
            rules.validar_execucao_em_embarque(execucao)
            rules.validar_chamada_concluida(execucao)

            alunos_resolvidos = []
            for cpf in cpfs or []:
                alunos_resolvidos.append(self._resolver_aluno_por_cpf(cpf))
            cpfs_limpos = [cpf_limpo for _aluno, cpf_limpo in alunos_resolvidos]
            rules.validar_cpfs_sem_duplicata(cpfs_limpos)
            if execucao.entradas_cpf_concluidas:
                rules.validar_replay_lote(
                    cpfs_limpos,
                    execucao.entradas_cpf_codigos or [],
                )
                return {
                    'entradas': self.object_instance.helper.listar_por_cpfs(
                        execucao,
                        cpfs_limpos,
                    ),
                    'replay': True,
                }
            if not alunos_resolvidos:
                return {'entradas': [], 'replay': False}

            resumo = execucao.business.obter_resumo_vagas()
            rules.validar_lote_cabe_nas_vagas(
                len(alunos_resolvidos),
                resumo['vagas_disponiveis'],
            )

            agora = timezone.now()
            entradas = []
            for aluno, cpf_limpo in alunos_resolvidos:
                ticket = self._aplicar_regras_elegibilidade(
                    execucao,
                    aluno,
                    bloquear_ticket=True,
                )
                if ticket is not None and ticket.status == StatusTicket.EM_ESPERA:
                    ticket.business.marcar_contemplado()
                entradas.append(
                    EntradaSemTicket.objects.create(
                        execucao_rota=execucao,
                        aluno=aluno,
                        cpf=cpf_limpo,
                        observacao='',
                        data_hora_entrada=agora,
                    )
                )
            execucao.entradas_cpf_concluidas = True
            execucao.entradas_cpf_concluidas_em = agora
            execucao.entradas_cpf_codigos = cpfs_limpos
            execucao.save(
                update_fields=[
                    'entradas_cpf_concluidas',
                    'entradas_cpf_concluidas_em',
                    'entradas_cpf_codigos',
                ],
            )
            return {'entradas': entradas, 'replay': False}
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível registrar a entrada sem ticket.',
                logger,
            )
