from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AprovarJustificativaView,
    DetalharJustificativaView,
    ListarJustificativasView,
    RejeitarJustificativaView,
)

urlpatterns = [
    path(
        'justificativas/',
        roteador_por_metodo(GET=ListarJustificativasView),
        name='justificativa-list',
    ),
    path(
        'justificativas/<int:pk>/',
        roteador_por_metodo(GET=DetalharJustificativaView),
        name='justificativa-detalhe',
    ),
    path(
        'justificativas/<int:pk>/aprovar/',
        roteador_por_metodo(POST=AprovarJustificativaView),
        name='justificativa-aprovar',
    ),
    path(
        'justificativas/<int:pk>/rejeitar/',
        roteador_por_metodo(POST=RejeitarJustificativaView),
        name='justificativa-rejeitar',
    ),
]
