from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarSetorView,
    CriarSetorView,
    DetalheSetorView,
    DesativarSetorView,
    ListarSetoresView,
    ReativarSetorView,
)

urlpatterns = [
    path('setores/', roteador_por_metodo(GET=ListarSetoresView, POST=CriarSetorView), name='setores'),
    path('setores/<int:pk>/', roteador_por_metodo(GET=DetalheSetorView, PATCH=AtualizarSetorView), name='setor-detalhe'),
    path('setores/<int:pk>/desativar/', DesativarSetorView.as_view(), name='setor-desativar'),
    path('setores/<int:pk>/reativar/', ReativarSetorView.as_view(), name='setor-reativar'),
]
