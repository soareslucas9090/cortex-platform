from AppCore.core.state.state import ModelInstanceState

from .choices import StatusTicket


class TicketState(ModelInstanceState):
    transicoes_permitidas = frozenset()

    def pode_transicionar_para(self, novo_status):
        return novo_status in self.transicoes_permitidas


class TicketReservadoState(TicketState):
    transicoes_permitidas = frozenset({
        StatusTicket.CANCELADO,
        StatusTicket.EMBARCADO,
        StatusTicket.AUSENTE,
    })


class TicketEmEsperaState(TicketState):
    transicoes_permitidas = frozenset({
        StatusTicket.RESERVADO,
        StatusTicket.CANCELADO,
    })


class TicketCanceladoState(TicketState):
    pass


class TicketEmbarcadoState(TicketState):
    pass


class TicketAusenteState(TicketState):
    pass


ESTADOS_TICKET = {
    StatusTicket.RESERVADO: TicketReservadoState,
    StatusTicket.EM_ESPERA: TicketEmEsperaState,
    StatusTicket.CANCELADO: TicketCanceladoState,
    StatusTicket.EMBARCADO: TicketEmbarcadoState,
    StatusTicket.AUSENTE: TicketAusenteState,
}

