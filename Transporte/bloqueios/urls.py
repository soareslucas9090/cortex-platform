from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    CriarJustificativaBloqueioView,
    DetalharBloqueioView,
    ListarBloqueiosView,
)

urlpatterns = [
    path(
        'bloqueios/',
        roteador_por_metodo(GET=ListarBloqueiosView),
        name='bloqueio-list',
    ),
    path(
        'bloqueios/<int:aluno_pk>/',
        roteador_por_metodo(GET=DetalharBloqueioView),
        name='bloqueio-detalhe',
    ),
    path(
        'bloqueios/justificativas/',
        roteador_por_metodo(POST=CriarJustificativaBloqueioView),
        name='bloqueio-justificativa-criar',
    ),
]
