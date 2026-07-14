from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    ConcederAutorizacaoView,
    DetalheAutorizacaoView,
    ListarAutorizacoesView,
    RevogarAutorizacaoView,
)

urlpatterns = [
    path(
        'autorizacoes/',
        roteador_por_metodo(GET=ListarAutorizacoesView, POST=ConcederAutorizacaoView),
        name='autorizacoes-list',
    ),
    path(
        'autorizacoes/<int:pk>/',
        roteador_por_metodo(GET=DetalheAutorizacaoView),
        name='autorizacao-detail',
    ),
    path(
        'autorizacoes/<int:pk>/revogar/',
        RevogarAutorizacaoView.as_view(),
        name='autorizacao-revogar',
    ),
]
