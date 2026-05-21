from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarVinculoFuncaoView,
    CriarVinculoView,
    DefinirResponsavelView,
    EncerrarVinculoView,
    ListarVinculosView,
    RemoverResponsavelView,
)

urlpatterns = [
    path('setores/<int:setor_pk>/vinculos/', roteador_por_metodo(GET=ListarVinculosView, POST=CriarVinculoView), name='vinculos'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/encerrar/', EncerrarVinculoView.as_view(), name='vinculo-encerrar'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/definir-responsavel/', DefinirResponsavelView.as_view(), name='vinculo-definir-responsavel'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/remover-responsavel/', RemoverResponsavelView.as_view(), name='vinculo-remover-responsavel'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/funcao/', AtualizarVinculoFuncaoView.as_view(), name='vinculo-atualizar-funcao'),
]
