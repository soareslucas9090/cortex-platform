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

app_name = 'cargos'

urlpatterns = [
    path('', roteador_por_metodo(GET=ListarCargosView, POST=CriarCargoView)),
    path('<int:pk>/', roteador_por_metodo(GET=DetalharCargoView, PATCH=AtualizarCargoView)),
    path('<int:pk>/desativar/', roteador_por_metodo(POST=DesativarCargoView)),
    path('<int:pk>/reativar/', roteador_por_metodo(POST=ReativarCargoView)),
]
