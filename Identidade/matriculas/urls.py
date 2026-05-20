from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AdicionarMatriculaView,
    DesativarMatriculaView,
    ListarMatriculasView,
)

urlpatterns = [
    path(
        'usuarios/<int:usuario_pk>/matriculas/',
        roteador_por_metodo(GET=ListarMatriculasView, POST=AdicionarMatriculaView),
        name='matriculas',
    ),
    path(
        'usuarios/<int:usuario_pk>/matriculas/<int:pk>/desativar/',
        DesativarMatriculaView.as_view(),
        name='matricula-desativar',
    ),
]
