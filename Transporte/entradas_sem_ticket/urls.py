from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import RegistrarEntradaSemTicketView

urlpatterns = [
    path(
        'execucoes-rotas/<int:pk>/conferencia/entradas-sem-ticket/',
        roteador_por_metodo(POST=RegistrarEntradaSemTicketView),
        name='conferencia-entrada-sem-ticket',
    ),
]
