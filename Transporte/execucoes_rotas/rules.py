from datetime import timedelta

from django.utils.timezone import localdate, now

from AppCore.core.exceptions.exceptions import NotFoundException
from AppCore.core.rules.rules import ModelInstanceRules
from Transporte.rotas.choices import DiaSemana

from .choices import StatusExecucaoRota

DIAS_SEMANA_PYTHON = {
    0: DiaSemana.SEGUNDA,
    1: DiaSemana.TERCA,
    2: DiaSemana.QUARTA,
    3: DiaSemana.QUINTA,
    4: DiaSemana.SEXTA,
    5: DiaSemana.SABADO,
    6: DiaSemana.DOMINGO,
}

MENSAGEM_EXECUCAO_DUPLICADA = 'Já existe uma execução desta rota para a data informada.'
MENSAGEM_MONITORAMENTO_APOS_FINALIZAR = (
    'Não é possível iniciar o monitoramento após finalizar a conferência.'
)
MENSAGEM_MONITORAMENTO_STATUS = (
    'Somente execuções abertas ou fechadas podem iniciar o embarque.'
)
MENSAGEM_MONITORAMENTO_T30 = (
    'O monitoramento só fica disponível após 30 minutos antes da saída.'
)


def execucao_elegivel_para_iniciar_monitoramento(execucao) -> bool:
    return (
        execucao.status in (StatusExecucaoRota.ABERTA, StatusExecucaoRota.FECHADA)
        and now() > execucao.data_hora_saida - timedelta(minutes=30)
    )


class ExecucaoRotaRules(ModelInstanceRules):

    def validar_rota_ativa(self, rota) -> bool:
        if not rota.ativo:
            self.return_exception('Não é possível criar uma execução para uma rota inativa.')
        if not rota.percurso.ativo:
            self.return_exception('Não é possível criar uma execução para um percurso inativo.')
        return True

    def validar_dia_da_rota(self, rota, data_execucao) -> bool:
        if DIAS_SEMANA_PYTHON[data_execucao.weekday()] != rota.dia_semana:
            self.return_exception('A data da execução não corresponde ao dia da semana da rota.')
        return True

    def validar_execucao_unica(self, existe_execucao) -> bool:
        if existe_execucao:
            self.return_exception(MENSAGEM_EXECUCAO_DUPLICADA)
        return True

    def validar_janela_monitoramento(self, execucao) -> bool:
        if execucao.status == StatusExecucaoRota.FINALIZADA:
            self.return_exception(MENSAGEM_MONITORAMENTO_APOS_FINALIZAR)
        if execucao_elegivel_para_iniciar_monitoramento(execucao):
            return True
        if execucao.status not in (StatusExecucaoRota.ABERTA, StatusExecucaoRota.FECHADA):
            self.return_exception(MENSAGEM_MONITORAMENTO_STATUS)
        self.return_exception(MENSAGEM_MONITORAMENTO_T30)

    def validar_chamada_para_finalizar(self, execucao) -> bool:
        if not execucao.chamada_tickets_concluida:
            self.return_exception(
                'Conclua a chamada dos tickets antes de finalizar a execução.'
            )
        return True

    def validar_execucao_em_embarque(self, execucao) -> bool:
        if execucao.status != StatusExecucaoRota.EM_EMBARQUE:
            self.return_exception('A conferência só opera execuções em embarque.')
        return True

    def validar_execucao_do_dia(self, execucao) -> bool:
        if (
            execucao.data_execucao != localdate()
            or execucao.status == StatusExecucaoRota.CANCELADA
        ):
            self.return_exception(
                'Execução não encontrada no escopo da conferência.',
                type_exception=NotFoundException,
            )
        return True

    def validar_ausentes_sem_duplicata(self, ausentes) -> bool:
        if len(ausentes) != len(set(ausentes)):
            self.return_exception('Há tickets duplicados na lista de ausentes.')
        return True

    def validar_replay_chamada(self, ausentes, persistidos) -> bool:
        if set(ausentes) != set(str(codigo) for codigo in persistidos):
            self.return_exception(
                'A chamada desta execução já foi concluída com outra classificação.',
            )
        return True

    def validar_cancelamento_antes_do_embarque(self, execucao) -> bool:
        if execucao.status == StatusExecucaoRota.EM_EMBARQUE:
            self.return_exception(
                'Não é possível cancelar uma execução em embarque. Finalize a conferência.',
            )
        if execucao.status == StatusExecucaoRota.FINALIZADA:
            self.return_exception('Não é possível cancelar uma execução já finalizada.')
        return True
