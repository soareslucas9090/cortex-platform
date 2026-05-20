from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AdicionarContatoView,
    AtualizarContatoView,
    ListarContatosView,
)

urlpatterns = [
    path(
        'usuarios/<int:usuario_pk>/contatos/',
        roteador_por_metodo(GET=ListarContatosView, POST=AdicionarContatoView),
        name='contatos',
    ),
    path(
        'usuarios/<int:usuario_pk>/contatos/<int:pk>/',
        roteador_por_metodo(PATCH=AtualizarContatoView),
        name='contato-detalhe',
    ),
]
