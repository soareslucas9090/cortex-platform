from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarSalaView,
    CriarSalaSetorView,
    CriarSalaView,
    DesativarSalaView,
    DetalheSalaView,
    ListarSalasView,
    ListarSalaSetorView,
    ReativarSalaView,
    RemoverSalaSetorView,
)

urlpatterns = [
    path('salas/', roteador_por_metodo(GET=ListarSalasView, POST=CriarSalaView), name='salas-list'),
    path('salas/<int:pk>/', roteador_por_metodo(GET=DetalheSalaView, PATCH=AtualizarSalaView), name='sala-detail'),
    path('salas/<int:pk>/desativar/', DesativarSalaView.as_view(), name='sala-desativar'),
    path('salas/<int:pk>/reativar/', ReativarSalaView.as_view(), name='sala-reativar'),
    path(
        'salas-setores/',
        roteador_por_metodo(GET=ListarSalaSetorView, POST=CriarSalaSetorView),
        name='salas-setores-list',
    ),
    path('salas-setores/<int:pk>/', RemoverSalaSetorView.as_view(), name='sala-setor-detail'),
]
