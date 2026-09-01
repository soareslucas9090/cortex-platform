from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AbrirReservasExecucaoRotaView,
    CancelarExecucaoRotaView,
    CriarExecucaoRotaView,
    DetalharExecucaoRotaView,
    FecharReservasExecucaoRotaView,
    FinalizarExecucaoRotaView,
    IniciarEmbarqueExecucaoRotaView,
    ListarExecucoesRotasView,
)

urlpatterns = [
    path(
        'execucoes-rotas/',
        roteador_por_metodo(GET=ListarExecucoesRotasView, POST=CriarExecucaoRotaView),
        name='execucao-rota-list',
    ),
    path(
        'execucoes-rotas/<int:pk>/',
        roteador_por_metodo(GET=DetalharExecucaoRotaView),
        name='execucao-rota-detalhe',
    ),
    path(
        'execucoes-rotas/<int:pk>/abrir-reservas/',
        roteador_por_metodo(POST=AbrirReservasExecucaoRotaView),
        name='execucao-rota-abrir-reservas',
    ),
    path(
        'execucoes-rotas/<int:pk>/fechar-reservas/',
        roteador_por_metodo(POST=FecharReservasExecucaoRotaView),
        name='execucao-rota-fechar-reservas',
    ),
    path(
        'execucoes-rotas/<int:pk>/iniciar-embarque/',
        roteador_por_metodo(POST=IniciarEmbarqueExecucaoRotaView),
        name='execucao-rota-iniciar-embarque',
    ),
    path(
        'execucoes-rotas/<int:pk>/finalizar/',
        roteador_por_metodo(POST=FinalizarExecucaoRotaView),
        name='execucao-rota-finalizar',
    ),
    path(
        'execucoes-rotas/<int:pk>/cancelar/',
        roteador_por_metodo(POST=CancelarExecucaoRotaView),
        name='execucao-rota-cancelar',
    ),
]
