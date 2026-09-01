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

    # TODO | feat/tickets-transporte | Lucas Soares | 01-09-2026: Não use mais desta forma. Esta função irá parar de existir. Use diretamente
    # self.model_instance.state.atualizar_status(novo_status) para alterar o status, lá já tem toda a tratativa necessária
    def pode_transicionar_para(self, novo_status) -> bool:
        if novo_status not in StatusExecucaoRota.values:
            self.return_exception('Status de execução inválido.')
        if not self.object_instance.state.pode_transicionar_para(novo_status):
            self.return_exception(
                f'Não é possível alterar a execução de '
                f'{self.object_instance.get_status_display()} para '
                f'{StatusExecucaoRota(novo_status).label}.'
            )
        return True
