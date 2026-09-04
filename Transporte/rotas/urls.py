from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarRotaView,
    CriarRotaView,
    DesativarRotaView,
    DetalharRotaView,
    ListarRotasView,
    ListarRotasDoDiaView,
    ReativarRotaView,
)

urlpatterns = [
    path('motorista/rotas-do-dia/', ListarRotasDoDiaView.as_view(), name='motorista-rotas-do-dia'),
    path('rotas/', roteador_por_metodo(GET=ListarRotasView, POST=CriarRotaView), name='rotas'),
    path('rotas/<int:pk>/', roteador_por_metodo(GET=DetalharRotaView, PATCH=AtualizarRotaView), name='rota-detalhe'),
    path('rotas/<int:pk>/desativar/', roteador_por_metodo(POST=DesativarRotaView), name='rota-desativar'),
    path('rotas/<int:pk>/reativar/', roteador_por_metodo(POST=ReativarRotaView), name='rota-reativar'),
]
