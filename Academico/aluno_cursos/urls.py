from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarAlunoCursosView,
    CriarAlunoCursoView,
    DetalharAlunoCursoView,
    AtualizarAlunoCursoView,
    EncerrarAlunoCursoView,
)

app_name = 'aluno_cursos'

urlpatterns = [
    path(
        '',
        roteador_por_metodo(GET=ListarAlunoCursosView, POST=CriarAlunoCursoView),
        name='aluno-curso-list',
    ),
    path(
        '<int:pk>/',
        roteador_por_metodo(GET=DetalharAlunoCursoView, PATCH=AtualizarAlunoCursoView),
        name='aluno-curso-detail',
    ),
    path(
        '<int:pk>/encerrar/',
        roteador_por_metodo(POST=EncerrarAlunoCursoView),
        name='aluno-curso-encerrar',
    ),
]
