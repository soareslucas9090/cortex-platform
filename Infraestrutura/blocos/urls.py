from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AtualizarBlocoView,
    CriarBlocoView,
    DesativarBlocoView,
    DetalheBlocoView,
    ListarBlocosView,
    ReativarBlocoView,
)

urlpatterns = [
    path('blocos/', roteador_por_metodo(GET=ListarBlocosView, POST=CriarBlocoView), name='blocos-list'),
    path('blocos/<int:pk>/', roteador_por_metodo(GET=DetalheBlocoView, PATCH=AtualizarBlocoView), name='bloco-detail'),
    path('blocos/<int:pk>/desativar/', DesativarBlocoView.as_view(), name='bloco-desativar'),
    path('blocos/<int:pk>/reativar/', ReativarBlocoView.as_view(), name='bloco-reativar'),
]
