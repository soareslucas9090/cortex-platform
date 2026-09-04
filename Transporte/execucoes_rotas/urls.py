from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AbrirReservasExecucaoRotaView,
    CancelarExecucaoRotaView,
    CriarExecucaoRotaView,
    DetalharExecucaoRotaView,
    FecharReservasExecucaoRotaView,
    FinalizarChamadaConferenciaView,
    FinalizarExecucaoRotaView,
    IniciarEmbarqueExecucaoRotaView,
    ListarExecucoesConferenciaView,
    ListarExecucoesRotasView,
    ListarFilaConferenciaView,
    ListarReservasConferenciaView,
    RemoverFilaConferenciaView,
)

urlpatterns = [
    path(
        'execucoes-rotas/',
        roteador_por_metodo(GET=ListarExecucoesRotasView, POST=CriarExecucaoRotaView),
        name='execucao-rota-list',
    ),
    path(
        'execucoes-rotas/conferencia/',
        roteador_por_metodo(GET=ListarExecucoesConferenciaView),
        name='conferencia-execucao-list',
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
        'execucoes-rotas/<int:pk>/cancelar/',
        roteador_por_metodo(POST=CancelarExecucaoRotaView),
        name='execucao-rota-cancelar',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/iniciar/',
        roteador_por_metodo(POST=IniciarEmbarqueExecucaoRotaView),
        name='conferencia-iniciar',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/finalizar/',
        roteador_por_metodo(POST=FinalizarExecucaoRotaView),
        name='conferencia-finalizar',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/reservas/',
        roteador_por_metodo(GET=ListarReservasConferenciaView),
        name='conferencia-reservas',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/finalizar-chamada/',
        roteador_por_metodo(POST=FinalizarChamadaConferenciaView),
        name='conferencia-finalizar-chamada',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/fila/',
        roteador_por_metodo(GET=ListarFilaConferenciaView),
        name='conferencia-fila',
    ),
    path(
        'execucoes-rotas/<int:pk>/conferencia/fila/<uuid:codigo>/remover/',
        roteador_por_metodo(POST=RemoverFilaConferenciaView),
        name='conferencia-fila-remover',
    ),
]
