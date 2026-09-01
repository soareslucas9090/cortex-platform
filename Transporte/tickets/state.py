from AppCore.core.state.state import ModelInstanceState

from .choices import StatusTicket


class TicketState(ModelInstanceState):
    transicoes_permitidas = frozenset()


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

