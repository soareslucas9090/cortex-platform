from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo
from .views import (
    ListarCursosView,
    CriarCursoView,
    DetalharCursoView,
    AtualizarCursoView,
    DesativarCursoView,
    ReativarCursoView,
)

urlpatterns = [
    path('cursos/', roteador_por_metodo(GET=ListarCursosView, POST=CriarCursoView), name='curso-list'),
    path('cursos/<int:pk>/', roteador_por_metodo(GET=DetalharCursoView, PATCH=AtualizarCursoView), name='curso-detail'),
    path('cursos/<int:pk>/desativar/', roteador_por_metodo(POST=DesativarCursoView), name='curso-desativar'),
    path('cursos/<int:pk>/reativar/', roteador_por_metodo(POST=ReativarCursoView), name='curso-reativar'),
]
