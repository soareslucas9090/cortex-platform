from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarCargosView,
    CriarCargoView,
    DetalharCargoView,
    AtualizarCargoView,
    DesativarCargoView,
    ReativarCargoView,
)

urlpatterns = [
    path('cargos/', roteador_por_metodo(GET=ListarCargosView, POST=CriarCargoView), name='cargo-list'),
    path('cargos/<int:pk>/', roteador_por_metodo(GET=DetalharCargoView, PATCH=AtualizarCargoView), name='cargo-detail'),
    path('cargos/<int:pk>/desativar/', roteador_por_metodo(POST=DesativarCargoView), name='cargo-desativar'),
    path('cargos/<int:pk>/reativar/', roteador_por_metodo(POST=ReativarCargoView), name='cargo-reativar'),
]
