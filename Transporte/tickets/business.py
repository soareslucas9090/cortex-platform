import logging

from django.core.signing import BadSignature
from django.db import IntegrityError, transaction
from django.utils import timezone

from AppCore.core.business.business import ModelInstanceBusiness
from AppCore.core.exceptions.exceptions import BusinessRuleException

from .choices import StatusTicket

logger = logging.getLogger(__name__)


class TicketBusiness(ModelInstanceBusiness):

    def listar_para_usuario(self, usuario):
        try:
            queryset = self.object_instance.helper.listar_com_relacionamentos()
            if getattr(usuario, 'tem_acesso_elevado', lambda: False)():
                return queryset
            aluno = getattr(usuario, 'aluno', None)
            return queryset.filter(aluno=aluno) if aluno is not None else queryset.none()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível listar os tickets.', logger)

    def solicitar_reserva(self, execucao_id, usuario):
        try:
            from Transporte.execucoes_rotas.models import ExecucaoRota

            from .models import Ticket

            with transaction.atomic():
                execucao = ExecucaoRota.objects.select_for_update().select_related(
                    'rota',
                    'rota__percurso',
                ).get(pk=execucao_id)
                rules = self.object_instance.rules
                aluno = rules.validar_aluno_elegivel(usuario)
                rules.validar_janela_solicitacao(execucao)
                rules.validar_ticket_inexistente(execucao, aluno)
                rules.validar_vaga_disponivel(execucao)
                return Ticket.objects.create(
                    execucao_rota=execucao,
                    aluno=aluno,
                    status=StatusTicket.RESERVADO,
                    reservado_em=timezone.now(),
                )
        except IntegrityError:
            raise BusinessRuleException('O aluno já possui um ticket ativo para esta execução.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível reservar o ticket.', logger)

    def entrar_fila(self, execucao_id, usuario):
        try:
            from Transporte.execucoes_rotas.models import ExecucaoRota

            from .models import Ticket

            with transaction.atomic():
                execucao = ExecucaoRota.objects.select_for_update().select_related(
                    'rota',
                    'rota__percurso',
                ).get(pk=execucao_id)
                rules = self.object_instance.rules
                aluno = rules.validar_aluno_elegivel(usuario)
                rules.validar_janela_solicitacao(execucao)
                rules.validar_ticket_inexistente(execucao, aluno)
                rules.validar_execucao_lotada(execucao)
                return Ticket.objects.create(
                    execucao_rota=execucao,
                    aluno=aluno,
                    status=StatusTicket.EM_ESPERA,
                    entrou_em_espera_em=timezone.now(),
                )
        except IntegrityError:
            raise BusinessRuleException('O aluno já possui um ticket ativo para esta execução.')
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível entrar na fila de espera.', logger)

    def obter_por_codigo(self, codigo, bloquear=False):
        try:
            from .models import Ticket

            queryset = Ticket.objects.select_related(
                'execucao_rota',
                'execucao_rota__rota',
                'execucao_rota__rota__percurso',
                'aluno',
                'aluno__usuario',
            )
            if bloquear:
                queryset = queryset.select_for_update()
            return queryset.get(codigo=codigo)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível obter o ticket.', logger)

    def cancelar(self, usuario):
        try:
            from Transporte.execucoes_rotas.models import ExecucaoRota

            from .models import Ticket

            with transaction.atomic():
                ticket_base = self.object_instance
                execucao = ExecucaoRota.objects.select_for_update().get(
                    pk=ticket_base.execucao_rota_id,
                )
                ticket = Ticket.objects.select_for_update().select_related(
                    'aluno__usuario',
                    'execucao_rota',
                ).get(pk=ticket_base.pk)
                ticket.rules.validar_dono_ou_admin(usuario)
                ticket.rules.validar_status(
                    StatusTicket.RESERVADO,
                    'Somente um ticket reservado pode ser cancelado por esta ação.',
                )
                ticket.rules.validar_limite_cancelamento()
                ticket.rules.pode_transicionar_para(StatusTicket.CANCELADO)
                ticket.status = StatusTicket.CANCELADO
                ticket.cancelado_em = timezone.now()
                ticket.save(update_fields=['status', 'cancelado_em', 'updated_at'])
                promovido = self.promover_proximo_da_fila(execucao)
                return ticket, promovido
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível cancelar o ticket.', logger)

    def sair_fila(self, usuario):
        try:
            from .models import Ticket

            with transaction.atomic():
                ticket = Ticket.objects.select_for_update().select_related(
                    'aluno__usuario',
                    'execucao_rota',
                ).get(pk=self.object_instance.pk)
                ticket.rules.validar_dono_ou_admin(usuario)
                ticket.rules.validar_status(
                    StatusTicket.EM_ESPERA,
                    'Somente um ticket em espera pode sair da fila.',
                )
                ticket.rules.validar_limite_cancelamento()
                ticket.rules.pode_transicionar_para(StatusTicket.CANCELADO)
                ticket.status = StatusTicket.CANCELADO
                ticket.cancelado_em = timezone.now()
                ticket.save(update_fields=['status', 'cancelado_em', 'updated_at'])
                return ticket
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível sair da fila de espera.', logger)

    def promover_proximo_da_fila(self, execucao):
        try:
            from .models import Ticket

            ticket = Ticket().helper.proximo_da_fila(execucao)
            if ticket is None:
                return None
            ticket.rules.pode_transicionar_para(StatusTicket.RESERVADO)
            ticket.status = StatusTicket.RESERVADO
            ticket.reservado_em = timezone.now()
            ticket.save(update_fields=['status', 'reservado_em', 'updated_at'])
            return ticket
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível promover o próximo ticket.', logger)

    def marcar_ausente(self):
        try:
            from Transporte.strikes.models import Strike

            from .models import Ticket

            with transaction.atomic():
                ticket = Ticket.objects.select_for_update().select_related(
                    'execucao_rota',
                    'aluno__usuario',
                ).get(pk=self.object_instance.pk)
                ticket.rules.pode_marcar_ausente()
                ticket.rules.pode_transicionar_para(StatusTicket.AUSENTE)
                ticket.status = StatusTicket.AUSENTE
                ticket.ausente_em = timezone.now()
                ticket.save(update_fields=['status', 'ausente_em', 'updated_at'])
                strike = Strike().business.criar_para_ticket(ticket)
                return ticket, strike
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível marcar a ausência.', logger)

    def gerar_codigo_qr(self):
        try:
            if not self.object_instance.pk:
                raise BusinessRuleException('O ticket precisa estar salvo para gerar o QR Code.')
            return self.object_instance.helper.gerar_codigo_qr()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível gerar o QR Code.', logger)

    def obter_posicao_fila(self):
        try:
            return self.object_instance.helper.obter_posicao_fila()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível calcular a posição na fila.', logger)

    def obter_posicao(self):
        try:
            return self.object_instance.helper.obter_posicao()
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível calcular a posição do ticket.', logger)

    def obter_posicoes_da_execucao(self, execucao):
        try:
            return self.object_instance.helper.obter_posicoes_execucao(execucao)
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível calcular as posições dos tickets.', logger)

    def validar_qr(self, codigo_qr):
        try:
            from .models import Ticket

            with transaction.atomic():
                try:
                    dados = Ticket().helper.decodificar_qr(codigo_qr)
                    codigo = dados['ticket']
                    execucao_id = dados['execucao']
                except (BadSignature, KeyError, TypeError):
                    raise BusinessRuleException('QR Code inválido ou adulterado.')

                ticket = Ticket.objects.select_for_update().select_related(
                    'execucao_rota',
                    'execucao_rota__rota',
                    'execucao_rota__rota__percurso',
                    'aluno__usuario',
                ).get(codigo=codigo)
                if ticket.execucao_rota_id != execucao_id:
                    raise BusinessRuleException('QR Code inválido para esta execução.')
                if ticket.status == StatusTicket.EMBARCADO:
                    return ticket, True
                ticket.rules.pode_validar_qr()
                ticket.rules.pode_transicionar_para(StatusTicket.EMBARCADO)
                ticket.status = StatusTicket.EMBARCADO
                ticket.embarcado_em = timezone.now()
                ticket.save(update_fields=['status', 'embarcado_em', 'updated_at'])
                return ticket, False
        except Exception as e:
            self.relancar_ou_erro_sistema(e, 'Não foi possível validar o QR Code.', logger)
