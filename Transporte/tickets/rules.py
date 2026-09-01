from datetime import timedelta

from django.utils.timezone import localtime, now

from Academico.alunos.choices import SituacaoAluno
from AppCore.core.rules.rules import ModelInstanceRules
from Transporte.execucoes_rotas.choices import StatusExecucaoRota
from Transporte.strikes.choices import StatusStrike

from .choices import StatusTicket


class TicketRules(ModelInstanceRules):

    def validar_aluno_elegivel(self, usuario):
        aluno = getattr(usuario, 'aluno', None)
        if not usuario.ativo or aluno is None or not aluno.ativo:
            self.return_exception('Somente um aluno ativo pode solicitar um ticket.')
        if aluno.situacao != SituacaoAluno.MATRICULADO:
            self.return_exception('Somente um aluno matriculado pode solicitar um ticket.')
        strikes_ativos = aluno.tickets_transporte.filter(
            strike__status=StatusStrike.ATIVO,
        ).count()
        if strikes_ativos >= 3:
            self.return_exception(
                'O aluno possui três ou mais strikes ativos e não pode solicitar novos tickets.'
            )
        return aluno

    def validar_execucao_aberta(self, execucao) -> bool:
        if execucao.status != StatusExecucaoRota.ABERTA:
            self.return_exception('As reservas desta execução não estão abertas.')
        return True

    def validar_janela_solicitacao(self, execucao) -> bool:
        self.validar_execucao_aberta(execucao)
        if execucao.data_execucao.weekday() >= 5:
            self.return_exception('Reservas e fila de espera funcionam somente de segunda a sexta.')

        agora = now()
        saida_local = localtime(execucao.data_hora_saida)
        abertura = saida_local.replace(hour=0, minute=0, second=0, microsecond=0)
        limite = execucao.data_hora_saida - timedelta(minutes=30)
        if agora < abertura:
            self.return_exception('As solicitações abrem à meia-noite do dia da execução.')
        if agora > limite:
            self.return_exception(
                'O prazo para reservar ou entrar na fila termina 30 minutos antes da saída.'
            )
        return True

    def validar_ticket_inexistente(self, execucao, aluno) -> bool:
        from .models import Ticket

        if Ticket.objects.filter(execucao_rota=execucao, aluno=aluno).exclude(
            status=StatusTicket.CANCELADO,
        ).exists():
            self.return_exception('O aluno já possui um ticket ativo para esta execução.')
        return True

    def validar_vaga_disponivel(self, execucao) -> bool:
        ocupadas = execucao.tickets.filter(status=StatusTicket.RESERVADO).count()
        if ocupadas >= execucao.quantidade_vagas:
            self.return_exception(
                'Não há vagas disponíveis. Solicite explicitamente a entrada na fila de espera.'
            )
        return True

    def validar_execucao_lotada(self, execucao) -> bool:
        ocupadas = execucao.tickets.filter(status=StatusTicket.RESERVADO).count()
        if ocupadas < execucao.quantidade_vagas:
            self.return_exception('Ainda há vagas disponíveis; solicite uma reserva direta.')
        return True

    def validar_dono_ou_admin(self, usuario) -> bool:
        dono = self.object_instance.aluno.usuario
        if dono == usuario or getattr(usuario, 'tem_acesso_elevado', lambda: False)():
            return True
        self.return_not_allowed('Você não tem permissão para alterar este ticket.')

    def validar_limite_cancelamento(self) -> bool:
        execucao = self.object_instance.execucao_rota
        self.validar_execucao_aberta(execucao)
        if execucao.data_execucao.weekday() >= 5:
            self.return_exception('Cancelamentos e saída da fila funcionam somente de segunda a sexta.')

        agora = now()
        saida_local = localtime(execucao.data_hora_saida)
        abertura = saida_local.replace(hour=0, minute=0, second=0, microsecond=0)
        limite = execucao.data_hora_saida - timedelta(minutes=30)
        if agora < abertura:
            self.return_exception('Cancelamentos e saída da fila abrem à meia-noite do dia da execução.')
        if agora > limite:
            self.return_exception(
                'O prazo para cancelar ou sair da fila termina 30 minutos antes da saída.'
            )
        return True

    def validar_status(self, status_esperado, mensagem) -> bool:
        if self.object_instance.status != status_esperado:
            self.return_exception(mensagem)
        return True

    def pode_transicionar_para(self, novo_status) -> bool:
        if novo_status not in StatusTicket.values:
            self.return_exception('Status de ticket inválido.')
        if not self.object_instance.state.pode_transicionar_para(novo_status):
            self.return_exception(
                f'Não é possível alterar o ticket de {self.object_instance.get_status_display()} '
                f'para {StatusTicket(novo_status).label}.'
            )
        return True

    def pode_marcar_ausente(self) -> bool:
        self.validar_status(
            StatusTicket.RESERVADO,
            'Somente um ticket reservado pode ser marcado como ausente.',
        )
        status_execucao = self.object_instance.execucao_rota.status
        if status_execucao not in (
            StatusExecucaoRota.EM_EMBARQUE,
            StatusExecucaoRota.FINALIZADA,
        ):
            self.return_exception(
                'A ausência só pode ser registrada durante o embarque ou após a finalização.'
            )
        return True

    def pode_validar_qr(self) -> bool:
        if self.object_instance.execucao_rota.status != StatusExecucaoRota.EM_EMBARQUE:
            self.return_exception('O QR Code só pode ser validado durante o embarque.')
        self.validar_status(
            StatusTicket.RESERVADO,
            'Este ticket não está disponível para embarque.',
        )
        return True
