from django.urls import path

from .views import (
    DesativarMatriculaView,
    DesativarUsuarioView,
    EnderecoView,
    ContatosView,
    ContatoView,
    MatriculasView,
    ReativarUsuarioView,
    UsuariosView,
    UsuarioView,
)

urlpatterns = [
    # Usuários
    path('usuarios/', UsuariosView.as_view(), name='usuarios'),
    path('usuarios/<int:pk>/', UsuarioView.as_view(), name='usuario-detalhe'),
    path('usuarios/<int:pk>/desativar/', DesativarUsuarioView.as_view(), name='usuario-desativar'),
    path('usuarios/<int:pk>/reativar/', ReativarUsuarioView.as_view(), name='usuario-reativar'),

    # Contatos
    path('usuarios/<int:usuario_pk>/contatos/', ContatosView.as_view(), name='contatos'),
    path('usuarios/<int:usuario_pk>/contatos/<int:pk>/', ContatoView.as_view(), name='contato-detalhe'),

    # Endereço
    path('usuarios/<int:usuario_pk>/endereco/', EnderecoView.as_view(), name='endereco'),

    # Matrículas
    path('usuarios/<int:usuario_pk>/matriculas/', MatriculasView.as_view(), name='matriculas'),
    path(
        'usuarios/<int:usuario_pk>/matriculas/<int:pk>/desativar/',
        DesativarMatriculaView.as_view(),
        name='matricula-desativar',
    ),
]
