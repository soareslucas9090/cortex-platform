from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    CancelarTicketView,
    DetalharTicketView,
    EntrarFilaEsperaView,
    ListarTicketsView,
    MarcarTicketAusenteView,
    ReservarTicketView,
    SairFilaEsperaView,
    ValidarQrTicketView,
)

urlpatterns = [
    path('tickets/', roteador_por_metodo(GET=ListarTicketsView), name='ticket-list'),
    path(
        'tickets/validar-qr/',
        roteador_por_metodo(POST=ValidarQrTicketView),
        name='ticket-validar-qr',
    ),
    path(
        'tickets/<uuid:codigo>/',
        roteador_por_metodo(GET=DetalharTicketView),
        name='ticket-detalhe',
    ),
    path(
        'tickets/<uuid:codigo>/cancelar/',
        roteador_por_metodo(POST=CancelarTicketView),
        name='ticket-cancelar',
    ),
    path(
        'tickets/<uuid:codigo>/sair-fila/',
        roteador_por_metodo(POST=SairFilaEsperaView),
        name='ticket-sair-fila',
    ),
    path(
        'tickets/<uuid:codigo>/marcar-ausente/',
        roteador_por_metodo(POST=MarcarTicketAusenteView),
        name='ticket-marcar-ausente',
    ),
    path(
        'execucoes-rotas/<int:pk>/reservar/',
        roteador_por_metodo(POST=ReservarTicketView),
        name='ticket-reservar',
    ),
    path(
        'execucoes-rotas/<int:pk>/fila-espera/entrar/',
        roteador_por_metodo(POST=EntrarFilaEsperaView),
        name='ticket-entrar-fila',
    ),
]
