from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import RegistrarEntradaSemTicketView, ValidarEntradaSemTicketView

urlpatterns = [
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/validar/',
        roteador_por_metodo(POST=ValidarEntradaSemTicketView),
        name='conferencia-entrada-sem-ticket-validar',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/',
        roteador_por_metodo(POST=RegistrarEntradaSemTicketView),
        name='conferencia-entrada-sem-ticket',
    ),
]
