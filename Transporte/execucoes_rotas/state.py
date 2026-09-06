from AppCore.core.state.state import ModelInstanceState

from .choices import StatusExecucaoRota


class ExecucaoRotaState(ModelInstanceState):
    status_choices_class = StatusExecucaoRota



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
        StatusExecucaoRota.EMBARCADO,
    })


class ExecucaoEmbarcadaState(ExecucaoRotaState):
    transicoes_permitidas = frozenset({
        StatusExecucaoRota.INICIADA,
    })


class ExecucaoIniciadaState(ExecucaoRotaState):
    transicoes_permitidas = frozenset({
        StatusExecucaoRota.FINALIZADA,
    })


class ExecucaoFinalizadaState(ExecucaoRotaState):
    pass


class ExecucaoCanceladaState(ExecucaoRotaState):
    pass


ESTADOS_EXECUCAO_ROTA = {
    StatusExecucaoRota.ABERTA: ExecucaoAbertaState,
    StatusExecucaoRota.FECHADA: ExecucaoFechadaState,
    StatusExecucaoRota.EM_EMBARQUE: ExecucaoEmEmbarqueState,
    StatusExecucaoRota.EMBARCADO: ExecucaoEmbarcadaState,
    StatusExecucaoRota.INICIADA: ExecucaoIniciadaState,
    StatusExecucaoRota.FINALIZADA: ExecucaoFinalizadaState,
    StatusExecucaoRota.CANCELADA: ExecucaoCanceladaState,
}
