from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarAlunosView,
    CriarAlunoView,
    DetalharAlunoView,
    AtualizarAlunoView,
)

urlpatterns = [
    path(
        '',
        roteador_por_metodo(
            GET=ListarAlunosView,
            POST=CriarAlunoView,
        ),
        name='aluno-list',
    ),
    path(
        '<int:usuario_id>/',
        roteador_por_metodo(
            GET=DetalharAlunoView,
            PATCH=AtualizarAlunoView,
        ),
        name='aluno-detail',
    ),
]

