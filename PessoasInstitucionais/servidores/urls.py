from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarServidoresView,
    CriarServidorView,
    DetalharServidorView,
    AtualizarServidorView,
    DesativarServidorView,
    ReativarServidorView,
)

urlpatterns = [
    path('', roteador_por_metodo(GET=ListarServidoresView, POST=CriarServidorView), name='servidor-list'),
    path('<int:pk>/', roteador_por_metodo(GET=DetalharServidorView, PATCH=AtualizarServidorView), name='servidor-detail'),
    path('<int:pk>/desativar/', roteador_por_metodo(POST=DesativarServidorView), name='servidor-desativar'),
    path('<int:pk>/reativar/', roteador_por_metodo(POST=ReativarServidorView), name='servidor-reativar'),
]
