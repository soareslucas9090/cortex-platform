from AppCore.core.state.state import ModelInstanceState

from .choices import StatusExecucaoRota


class ExecucaoRotaState(ModelInstanceState):
    transicoes_permitidas = frozenset()

    def pode_transicionar_para(self, novo_status):
        return novo_status in self.transicoes_permitidas


class ExecucaoAbertaState(ExecucaoRotaState):
    transicoes_permitidas = frozenset({
        StatusExecucaoRota.FECHADA,
        StatusExecucaoRota.EM_EMBARQUE,
        StatusExecucaoRota.CANCELADA,
    })


class ExecucaoFechadaState(ExecucaoRotaState):
    transicoes_permitidas = frozenset({
        StatusExecucaoRota.ABERTA,
        StatusExecucaoRota.EM_EMBARQUE,
        StatusExecucaoRota.CANCELADA,
    })


class ExecucaoEmEmbarqueState(ExecucaoRotaState):
    transicoes_permitidas = frozenset({
        StatusExecucaoRota.FINALIZADA,
        StatusExecucaoRota.CANCELADA,
    })


class ExecucaoFinalizadaState(ExecucaoRotaState):
    pass


class ExecucaoCanceladaState(ExecucaoRotaState):
    pass


ESTADOS_EXECUCAO_ROTA = {
    StatusExecucaoRota.ABERTA: ExecucaoAbertaState,
    StatusExecucaoRota.FECHADA: ExecucaoFechadaState,
    StatusExecucaoRota.EM_EMBARQUE: ExecucaoEmEmbarqueState,
    StatusExecucaoRota.FINALIZADA: ExecucaoFinalizadaState,
    StatusExecucaoRota.CANCELADA: ExecucaoCanceladaState,
}

