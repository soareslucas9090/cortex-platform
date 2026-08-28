from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarPercursoView,
    CriarPercursoView,
    DesativarPercursoView,
    DetalharPercursoView,
    ListarPercursosView,
    ReativarPercursoView,
)

urlpatterns = [
    path('percursos/', roteador_por_metodo(GET=ListarPercursosView, POST=CriarPercursoView), name='percursos'),
    path('percursos/<int:pk>/', roteador_por_metodo(GET=DetalharPercursoView, PATCH=AtualizarPercursoView), name='percurso-detalhe'),
    path('percursos/<int:pk>/desativar/', roteador_por_metodo(POST=DesativarPercursoView), name='percurso-desativar'),
    path('percursos/<int:pk>/reativar/', roteador_por_metodo(POST=ReativarPercursoView), name='percurso-reativar'),
]
