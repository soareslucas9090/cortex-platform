from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AceitarSolicitacaoTrocaTitularView,
    CancelarSolicitacaoTrocaTitularView,
    CriarSolicitacaoTrocaTitularView,
    DetalheEmprestimoView,
    DevolverItensEmprestimoView,
    ListarEmprestimosView,
    ListarResponsaveisElegiveisView,
    ListarSolicitacoesTrocaTitularView,
    ListarSolicitantesElegiveisView,
    RealizarEmprestimoView,
    RecusarSolicitacaoTrocaTitularView,
    TrocarTitularEmprestimoView,
)

urlpatterns = [
    path(
        'emprestimos/solicitantes-elegiveis/',
        ListarSolicitantesElegiveisView.as_view(),
        name='emprestimos-solicitantes-elegiveis',
    ),
    path(
        'emprestimos/responsaveis-elegiveis/',
        ListarResponsaveisElegiveisView.as_view(),
        name='emprestimos-responsaveis-elegiveis',
    ),
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
    path(
        'emprestimos/<int:emprestimo_id>/solicitacoes-troca/',
        CriarSolicitacaoTrocaTitularView.as_view(),
        name='emprestimo-solicitacao-troca-criar',
    ),
    path(
        'solicitacoes-troca/',
        ListarSolicitacoesTrocaTitularView.as_view(),
        name='solicitacao-troca-list',
    ),
    path(
        'solicitacoes-troca/<int:pk>/aceitar/',
        AceitarSolicitacaoTrocaTitularView.as_view(),
        name='solicitacao-troca-aceitar',
    ),
    path(
        'solicitacoes-troca/<int:pk>/recusar/',
        RecusarSolicitacaoTrocaTitularView.as_view(),
        name='solicitacao-troca-recusar',
    ),
    path(
        'solicitacoes-troca/<int:pk>/cancelar/',
        CancelarSolicitacaoTrocaTitularView.as_view(),
        name='solicitacao-troca-cancelar',
    ),
]
