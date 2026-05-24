from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarUsuarioView,
    CriarUsuarioView,
    DetalheUsuarioView,
    DesativarUsuarioView,
    ListarUsuariosView,
    ReativarUsuarioView,
)

urlpatterns = [
    path('usuarios/', roteador_por_metodo(GET=ListarUsuariosView, POST=CriarUsuarioView), name='usuario-list'),
    path('usuarios/<int:pk>/', roteador_por_metodo(GET=DetalheUsuarioView, PATCH=AtualizarUsuarioView), name='usuario-detail'),
    path('usuarios/<int:pk>/desativar/', DesativarUsuarioView.as_view(), name='usuario-desativar'),
    path('usuarios/<int:pk>/reativar/', ReativarUsuarioView.as_view(), name='usuario-reativar'),
]
