from datetime import timedelta

from django.utils.timezone import now

from Transporte.rotas.choices import DiaSemana

from AppCore.core.rules.rules import ModelInstanceRules

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
        if execucao.status not in (StatusExecucaoRota.ABERTA, StatusExecucaoRota.FECHADA):
            self.return_exception('Somente execuções abertas ou fechadas podem iniciar o embarque.')
        if now() < execucao.data_hora_saida - timedelta(minutes=30):
            self.return_exception(
                'O monitoramento só fica disponível 30 minutos antes da saída.'
            )
        return True

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
