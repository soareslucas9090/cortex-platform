import logging
from datetime import datetime

from django.db import IntegrityError
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

from .choices import StatusExecucaoRota
from .rules import MENSAGEM_EXECUCAO_DUPLICADA

logger = logging.getLogger(__name__)


class ExecucaoRotaBusiness(ModelInstanceBusiness):

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

    def obter_para_conferencia(self, execucao_id, exigir_embarque=False, usuario=None):
        try:
            return self.object_instance.helper.obter_para_conferencia(
                execucao_id,
                exigir_embarque=exigir_embarque,
                usuario=usuario,
            )
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
            execucao.rules.validar_janela_monitoramento(execucao)
            return execucao.state.atualizar_status(StatusExecucaoRota.EM_EMBARQUE)
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
            if execucao.chamada_tickets_concluida:
                return execucao

            ausentes = list(ausentes or [])
            tickets = list(
                Ticket.objects.select_for_update().select_related(
                    'execucao_rota',
                    'aluno__usuario',
                ).filter(
                    execucao_rota=execucao,
                    status=StatusTicket.RESERVADO,
                )
            )
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

            execucao.chamada_tickets_concluida = True
            execucao.save(update_fields=['chamada_tickets_concluida'])
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
            execucao.rules.validar_execucao_em_embarque(execucao)
            execucao.rules.validar_chamada_para_finalizar(execucao)
            Ticket().business.encerrar_fila_na_finalizacao(execucao)
            return execucao.state.atualizar_status(StatusExecucaoRota.FINALIZADA)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível finalizar a execução.', logger)
