from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarRecursoView,
    CriarRecursoView,
    DesativarRecursoView,
    DetalheRecursoView,
    EnviarFotoRecursoView,
    ListarRecursosView,
    ObterFotoRecursoView,
    ReativarRecursoView,
    RemoverFotoRecursoView,
)

urlpatterns = [
    path('recursos/', roteador_por_metodo(GET=ListarRecursosView, POST=CriarRecursoView), name='recursos-list'),
    path('recursos/<int:pk>/', roteador_por_metodo(GET=DetalheRecursoView, PATCH=AtualizarRecursoView), name='recurso-detail'),
    path(
        'recursos/<int:pk>/foto/',
        roteador_por_metodo(
            GET=ObterFotoRecursoView,
            POST=EnviarFotoRecursoView,
            DELETE=RemoverFotoRecursoView,
        ),
        name='recurso-foto',
    ),
    path('recursos/<int:pk>/desativar/', DesativarRecursoView.as_view(), name='recurso-desativar'),
    path('recursos/<int:pk>/reativar/', ReativarRecursoView.as_view(), name='recurso-reativar'),
]
