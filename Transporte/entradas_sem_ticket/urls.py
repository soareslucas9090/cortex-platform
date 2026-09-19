from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AdicionarRascunhoEntradaSemTicketView,
    ListarRascunhoEntradaSemTicketView,
    RegistrarEntradaSemTicketView,
    RemoverRascunhoEntradaSemTicketView,
    ValidarEntradaSemTicketView,
)

urlpatterns = [
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/validar/',
        roteador_por_metodo(POST=ValidarEntradaSemTicketView),
        name='conferencia-entrada-sem-ticket-validar',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/rascunho/',
        roteador_por_metodo(
            GET=ListarRascunhoEntradaSemTicketView,
            POST=AdicionarRascunhoEntradaSemTicketView,
        ),
        name='conferencia-entrada-sem-ticket-rascunho',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/rascunho/remover/',
        roteador_por_metodo(POST=RemoverRascunhoEntradaSemTicketView),
        name='conferencia-entrada-sem-ticket-rascunho-remover',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/',
        roteador_por_metodo(POST=RegistrarEntradaSemTicketView),
        name='conferencia-entrada-sem-ticket',
    ),
]
