from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import DetalheTipoAutorizacaoView, ListarTiposAutorizacaoView

urlpatterns = [
    path(
        'tipos/',
        roteador_por_metodo(GET=ListarTiposAutorizacaoView),
        name='tipo-autorizacao-list',
    ),
    path(
        'tipos/<int:pk>/',
        roteador_por_metodo(GET=DetalheTipoAutorizacaoView),
        name='tipo-autorizacao-detail',
    ),
]
