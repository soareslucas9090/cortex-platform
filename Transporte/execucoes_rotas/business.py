import logging
from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

from .choices import StatusExecucaoRota
from .rules import MENSAGEM_EXECUCAO_DUPLICADA

logger = logging.getLogger(__name__)


class ExecucaoRotaBusiness(ModelInstanceBusiness):

    def listar_historico(self, usuario, filtros=None):
        try:
            from Transporte.permissoes.access import usuario_pode_operar_rota

            self.object_instance.rules.validar_acesso_historico(usuario_pode_operar_rota(usuario))
            return self.object_instance.helper.listar_historico(filtros)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar o histórico de rotas.', logger)

    def listar_percursos_historico(self, usuario):
        try:
            from Transporte.permissoes.access import usuario_pode_operar_rota

            self.object_instance.rules.validar_acesso_historico(usuario_pode_operar_rota(usuario))
            return self.object_instance.helper.listar_percursos_historico()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os percursos do histórico.', logger)

    def detalhar_historico(self, usuario, execucao_id):
        try:
            from Transporte.permissoes.access import usuario_pode_operar_rota

            self.object_instance.rules.validar_acesso_historico(usuario_pode_operar_rota(usuario))
            return self.object_instance.helper.detalhar_historico(execucao_id)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter os detalhes da rota executada.', logger)

    @transaction.atomic
    def operar_rota(self, execucao_id, usuario, finalizar=False):
        """Registra a viagem sob bloqueio, preservando horários em reenvios."""
        try:
            from AppCore.core.exceptions.exceptions import AuthorizationException
            from Transporte.permissoes.access import usuario_pode_operar_rota

            if not usuario_pode_operar_rota(usuario):
                raise AuthorizationException('Acesso permitido somente a motoristas ativos e administradores.')
            execucao = self.object_instance.helper.obter_por_id(execucao_id, bloquear=True)
            if finalizar:
                execucao.rules.validar_finalizacao_rota(execucao)
                execucao.rules.validar_responsavel_rota(execucao, usuario)
                if execucao.rota_finalizada_em is None:
                    execucao.rota_finalizada_em = timezone.now()
                    execucao.save(update_fields=['rota_finalizada_em'])
            else:
                execucao.rules.validar_inicio_rota(execucao)
                if execucao.rota_iniciada_em is not None:
                    execucao.rules.validar_responsavel_rota(execucao, usuario)
                    return execucao
                execucao.rota_iniciada_em = timezone.now()
                execucao.rota_iniciada_por = usuario
                execucao.save(update_fields=['rota_iniciada_em', 'rota_iniciada_por'])
            return execucao
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível registrar a operação da rota.', logger)

    def listar_para_usuario(self, usuario, status_param=None, data_param=None):
        try:
            return self.object_instance.helper.listar_para_usuario(
                usuario,
                status_param,
                data_param,
            )
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar as execuções de rota.', logger)

    def obter_resumo_vagas(self):
        try:
            ocupadas = self.object_instance.helper.contar_vagas_ocupadas()
            return {
                'vagas_ocupadas': ocupadas,
                'vagas_disponiveis': max(self.object_instance.quantidade_vagas - ocupadas, 0),
            }
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível calcular as vagas da execução.', logger)

    def pode_monitorar(self) -> bool:
        try:
            return self.object_instance.helper.pode_monitorar()
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível verificar se o monitoramento pode ser iniciado.',
                logger,
            )

    def criar_execucao(self, rota_id, data_execucao):
        try:
            from Transporte.rotas.models import Rota

            from .models import ExecucaoRota

            rota = Rota.objects.select_related('percurso').get(pk=rota_id)
            rules = self.object_instance.rules
            rules.validar_rota_ativa(rota)
            rules.validar_dia_da_rota(rota, data_execucao)
            rules.validar_execucao_unica(
                self.object_instance.helper.existe_para_rota_na_data(rota_id, data_execucao),
            )
            data_hora_saida = timezone.make_aware(
                datetime.combine(data_execucao, rota.horario_saida),
                timezone.get_current_timezone(),
            )
            return ExecucaoRota.objects.create(
                rota=rota,
                data_execucao=data_execucao,
                data_hora_saida=data_hora_saida,
                quantidade_vagas=rota.quantidade_vagas,
            )
        except IntegrityError:
            raise BusinessRuleException(MENSAGEM_EXECUCAO_DUPLICADA)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível criar a execução da rota.', logger)

    def obter_por_id(self, execucao_id, bloquear=False):
        try:
            return self.object_instance.helper.obter_por_id(execucao_id, bloquear)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter a execução da rota.', logger)

    def alterar_status(self, novo_status):
        try:
            execucao = self.object_instance.helper.obter_por_id(
                self.object_instance.pk,
                bloquear=True,
            )
            if novo_status == StatusExecucaoRota.CANCELADA:
                execucao.rules.validar_cancelamento_antes_do_embarque(execucao)
            return execucao.state.atualizar_status(novo_status)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível alterar o status da execução.', logger)

    def listar_para_conferencia(self, data_param=None):
        try:
            return self.object_instance.helper.listar_para_conferencia(data_param)
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível listar as execuções da conferência.',
                logger,
            )

    def obter_para_conferencia(self, execucao_id, exigir_embarque=False):
        try:
            execucao = self.object_instance.helper.obter_por_id(execucao_id)
            execucao.rules.validar_execucao_do_dia(execucao)
            if exigir_embarque:
                execucao.rules.validar_filas_apos_monitoramento(execucao)
            return execucao
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível obter a execução da conferência.',
                logger,
            )

    def iniciar_embarque(self):
        try:
            execucao = self.object_instance.helper.obter_por_id(
                self.object_instance.pk,
                bloquear=True,
            )
            if execucao.status == StatusExecucaoRota.EM_EMBARQUE:
                return execucao
            execucao.rules.validar_janela_monitoramento(execucao)
            execucao = execucao.state.atualizar_status(StatusExecucaoRota.EM_EMBARQUE)
            if execucao.monitoramento_iniciado_em is None:
                execucao.monitoramento_iniciado_em = timezone.now()
                execucao.save(update_fields=['monitoramento_iniciado_em'])
            return execucao
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível iniciar o embarque.', logger)

    def finalizar_chamada(self, ausentes):
        try:
            from Transporte.tickets.choices import StatusTicket
            from Transporte.tickets.models import Ticket

            execucao = self.object_instance.helper.obter_por_id(
                self.object_instance.pk,
                bloquear=True,
            )
            execucao.rules.validar_execucao_em_embarque(execucao)
            ausentes = [str(codigo) for codigo in (ausentes or [])]
            execucao.rules.validar_ausentes_sem_duplicata(ausentes)

            if execucao.chamada_tickets_concluida:
                execucao.rules.validar_replay_chamada(
                    ausentes,
                    execucao.chamada_ausentes_codigos or [],
                )
                return execucao

            tickets = list(Ticket().helper.listar_reservados_bloqueados(execucao))
            por_codigo = {str(ticket.codigo): ticket for ticket in tickets}
            for codigo in ausentes:
                ticket = por_codigo.get(str(codigo))
                if ticket is None:
                    raise BusinessRuleException(
                        'Um dos tickets informados não está reservado nesta execução.',
                    )
                ticket.business.marcar_ausente()

            for ticket in tickets:
                ticket.refresh_from_db()
                if ticket.status != StatusTicket.RESERVADO:
                    continue
                ticket.embarcado_em = timezone.now()
                ticket.state.atualizar_status(StatusTicket.EMBARCADO)

            agora = timezone.now()
            execucao.chamada_tickets_concluida = True
            execucao.chamada_concluida_em = agora
            execucao.chamada_ausentes_codigos = ausentes
            execucao.save(
                update_fields=[
                    'chamada_tickets_concluida',
                    'chamada_concluida_em',
                    'chamada_ausentes_codigos',
                ],
            )
            return execucao
        except Exception as e:
            self.relancar_ou_erro_sistema(
                e,
                'Não foi possível finalizar a chamada dos tickets.',
                logger,
            )

    def finalizar_conferencia(self):
        try:
            from Transporte.tickets.models import Ticket

            execucao = self.object_instance.helper.obter_por_id(
                self.object_instance.pk,
                bloquear=True,
            )
            if execucao.status == StatusExecucaoRota.FINALIZADA:
                return execucao
            execucao.rules.validar_execucao_em_embarque(execucao)
            execucao.rules.validar_chamada_para_finalizar(execucao)
            Ticket().business.encerrar_fila_na_finalizacao(execucao)
            execucao = execucao.state.atualizar_status(StatusExecucaoRota.FINALIZADA)
            execucao.finalizada_em = timezone.now()
            execucao.save(update_fields=['finalizada_em'])
            return execucao
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível finalizar a execução.', logger)
