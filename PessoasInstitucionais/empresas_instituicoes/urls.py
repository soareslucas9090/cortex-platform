from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarEmpresasView,
    CriarEmpresaView,
    DetalharEmpresaView,
    AtualizarEmpresaView,
    DesativarEmpresaView,
    ReativarEmpresaView,
)

urlpatterns = [
    path('', roteador_por_metodo(GET=ListarEmpresasView, POST=CriarEmpresaView)),
    path('<int:pk>/', roteador_por_metodo(GET=DetalharEmpresaView, PATCH=AtualizarEmpresaView)),
    path('<int:pk>/desativar/', roteador_por_metodo(POST=DesativarEmpresaView)),
    path('<int:pk>/reativar/', roteador_por_metodo(POST=ReativarEmpresaView)),
]
