from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarAlunoCursosView,
    CriarAlunoCursoView,
    DetalharAlunoCursoView,
    AtualizarAlunoCursoView,
    EncerrarAlunoCursoView,
)

urlpatterns = [
    path(
        'aluno-cursos/',
        roteador_por_metodo(GET=ListarAlunoCursosView, POST=CriarAlunoCursoView),
        name='aluno-curso-list',
    ),
    path(
        'aluno-cursos/<int:pk>/',
        roteador_por_metodo(GET=DetalharAlunoCursoView, PATCH=AtualizarAlunoCursoView),
        name='aluno-curso-detail',
    ),
    path(
        'aluno-cursos/<int:pk>/encerrar/',
        roteador_por_metodo(POST=EncerrarAlunoCursoView),
        name='aluno-curso-encerrar',
    ),
]
