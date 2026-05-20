from django.urls import path

from django.urls import path

from .views import (
    AtualizarVinculoFuncaoView,
    DefinirResponsavelView,
    DesativarFuncaoView,
    DesativarSetorView,
    EncerrarVinculoView,
    FuncoesView,
    FuncaoView,
    ReativarFuncaoView,
    ReativarSetorView,
    RemoverResponsavelView,
    SetoresView,
    SetorView,
    VinculosView,
)

urlpatterns = [
    # Setores
    path('setores/', SetoresView.as_view(), name='setores'),
    path('setores/<int:pk>/', SetorView.as_view(), name='setor-detalhe'),
    path('setores/<int:pk>/desativar/', DesativarSetorView.as_view(), name='setor-desativar'),
    path('setores/<int:pk>/reativar/', ReativarSetorView.as_view(), name='setor-reativar'),

    # Vínculos de setor
    path('setores/<int:setor_pk>/vinculos/', VinculosView.as_view(), name='vinculos'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/encerrar/', EncerrarVinculoView.as_view(), name='vinculo-encerrar'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/definir-responsavel/', DefinirResponsavelView.as_view(), name='vinculo-definir-responsavel'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/remover-responsavel/', RemoverResponsavelView.as_view(), name='vinculo-remover-responsavel'),
    path('setores/<int:setor_pk>/vinculos/<int:pk>/funcao/', AtualizarVinculoFuncaoView.as_view(), name='vinculo-atualizar-funcao'),

    # Funções
    path('funcoes/', FuncoesView.as_view(), name='funcoes'),
    path('funcoes/<int:pk>/', FuncaoView.as_view(), name='funcao-detalhe'),
    path('funcoes/<int:pk>/desativar/', DesativarFuncaoView.as_view(), name='funcao-desativar'),
    path('funcoes/<int:pk>/reativar/', ReativarFuncaoView.as_view(), name='funcao-reativar'),
]
