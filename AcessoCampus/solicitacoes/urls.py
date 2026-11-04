from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AceitarSolicitacaoView,
    AutorizarAcessoView,
    DetalharSolicitacaoView,
    ListarAlunosElegiveisView,
    ListarSolicitacoesView,
    ListarTurmasView,
    RecusarSolicitacaoView,
)

urlpatterns = [
    path(
        'alunos/',
        roteador_por_metodo(GET=ListarAlunosElegiveisView),
        name='aluno-elegivel-list',
    ),
    path(
        'turmas/',
        roteador_por_metodo(GET=ListarTurmasView),
        name='turma-list',
    ),
    path(
        'autorizacoes/',
        roteador_por_metodo(POST=AutorizarAcessoView),
        name='autorizacao-criar',
    ),
    path(
        'solicitacoes/',
        roteador_por_metodo(GET=ListarSolicitacoesView),
        name='solicitacao-list',
    ),
    path(
        'solicitacoes/<int:pk>/',
        roteador_por_metodo(GET=DetalharSolicitacaoView),
        name='solicitacao-detail',
    ),
    path(
        'solicitacoes/<int:pk>/aceitar/',
        roteador_por_metodo(POST=AceitarSolicitacaoView),
        name='solicitacao-aceitar',
    ),
    path(
        'solicitacoes/<int:pk>/recusar/',
        roteador_por_metodo(POST=RecusarSolicitacaoView),
        name='solicitacao-recusar',
    ),
]
