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
    path('', roteador_por_metodo(GET=ListarEmpresasView, POST=CriarEmpresaView), name='empresa-list'),
    path('<int:pk>/', roteador_por_metodo(GET=DetalharEmpresaView, PATCH=AtualizarEmpresaView), name='empresa-detail'),
    path('<int:pk>/desativar/', roteador_por_metodo(POST=DesativarEmpresaView), name='empresa-desativar'),
    path('<int:pk>/reativar/', roteador_por_metodo(POST=ReativarEmpresaView), name='empresa-reativar'),
]
