from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarFuncaoView,
    CriarFuncaoView,
    DetalheFuncaoView,
    DesativarFuncaoView,
    ListarFuncoesView,
    ReativarFuncaoView,
)

urlpatterns = [
    path('funcoes/', roteador_por_metodo(GET=ListarFuncoesView, POST=CriarFuncaoView), name='funcoes'),
    path('funcoes/<int:pk>/', roteador_por_metodo(GET=DetalheFuncaoView, PATCH=AtualizarFuncaoView), name='funcao-detalhe'),
    path('funcoes/<int:pk>/desativar/', DesativarFuncaoView.as_view(), name='funcao-desativar'),
    path('funcoes/<int:pk>/reativar/', ReativarFuncaoView.as_view(), name='funcao-reativar'),
]
