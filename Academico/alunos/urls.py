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
        'alunos/',
        roteador_por_metodo(
            GET=ListarAlunosView,
            POST=CriarAlunoView,
        ),
        name='aluno-list',
    ),
    path(
        'alunos/<int:usuario_id>/',
        roteador_por_metodo(
            GET=DetalharAlunoView,
            PATCH=AtualizarAlunoView,
        ),
        name='aluno-detail',
    ),
]

