from django.urls import path

from .views import (
    ContadorNaoLidasView,
    ListarNotificacoesView,
    MarcarNotificacaoLidaView,
    MarcarTodasLidasView,
)

urlpatterns = [
    path('', ListarNotificacoesView.as_view(), name='notificacao-list'),
    path(
        'nao-lidas/contador/',
        ContadorNaoLidasView.as_view(),
        name='notificacao-nao-lidas-contador',
    ),
    path(
        'marcar-todas-lidas/',
        MarcarTodasLidasView.as_view(),
        name='notificacao-marcar-todas-lidas',
    ),
    path(
        '<int:pk>/lida/',
        MarcarNotificacaoLidaView.as_view(),
        name='notificacao-lida',
    ),
]
