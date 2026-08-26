from django.urls import path

from .views import (
    BaixarModeloImportacaoInfraestruturaView,
    CancelarImportacaoView,
    HistoricoImportacaoLoteView,
    ImportarInfraestruturaLoteView,
    PreVisualizarImportacaoInfraestruturaView,
    StatusImportacaoLoteView,
)

urlpatterns = [
    path(
        'importacao/modelo/',
        BaixarModeloImportacaoInfraestruturaView.as_view(),
        name='importacao-modelo',
    ),
    path(
        'importacao/pre-visualizar/',
        PreVisualizarImportacaoInfraestruturaView.as_view(),
        name='importacao-pre-visualizar',
    ),
    path(
        'importacao/status/',
        StatusImportacaoLoteView.as_view(),
        name='importacao-status',
    ),
    path(
        'importacao/cancelar/',
        CancelarImportacaoView.as_view(),
        name='importacao-cancelar',
    ),
    path(
        'importacao/historico/',
        HistoricoImportacaoLoteView.as_view(),
        name='importacao-historico',
    ),
    path(
        'importacao/',
        ImportarInfraestruturaLoteView.as_view(),
        name='importacao',
    ),
]
