from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarTerceirizadosView,
    CriarTerceirizadoView,
    DetalharTerceirizadoView,
    AtualizarTerceirizadoView,
    DesativarTerceirizadoView,
    ReativarTerceirizadoView,
)

urlpatterns = [
    path('terceirizados/', roteador_por_metodo(GET=ListarTerceirizadosView, POST=CriarTerceirizadoView), name='terceirizado-list'),
    path('terceirizados/<int:pk>/', roteador_por_metodo(GET=DetalharTerceirizadoView, PATCH=AtualizarTerceirizadoView), name='terceirizado-detail'),
    path('terceirizados/<int:pk>/desativar/', roteador_por_metodo(POST=DesativarTerceirizadoView), name='terceirizado-desativar'),
    path('terceirizados/<int:pk>/reativar/', roteador_por_metodo(POST=ReativarTerceirizadoView), name='terceirizado-reativar'),
]
