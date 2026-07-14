from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    DetalheEmprestimoView,
    DevolverItensEmprestimoView,
    ListarEmprestimosView,
    RealizarEmprestimoView,
    TrocarTitularEmprestimoView,
)

urlpatterns = [
    path(
        'emprestimos/',
        roteador_por_metodo(GET=ListarEmprestimosView, POST=RealizarEmprestimoView),
        name='emprestimos-list',
    ),
    path(
        'emprestimos/<int:pk>/',
        roteador_por_metodo(GET=DetalheEmprestimoView),
        name='emprestimo-detail',
    ),
    path(
        'emprestimos/<int:pk>/devolver/',
        DevolverItensEmprestimoView.as_view(),
        name='emprestimo-devolver',
    ),
    path(
        'emprestimos/<int:pk>/trocar-titular/',
        TrocarTitularEmprestimoView.as_view(),
        name='emprestimo-trocar-titular',
    ),
]
