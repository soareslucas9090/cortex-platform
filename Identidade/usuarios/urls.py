from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    AdicionarItemColetivoView,
    AtualizarUsuarioView,
    AtualizarFotoPrimariaView,
    ObterFotoSecundariaView,
    AtualizarFotoSecundariaView,
    RemoverFotoSecundariaView,
    CriarUsuarioView,
    DetalheUsuarioView,
    DesativarUsuarioView,
    DocumentarPermissoesView,
    ListarUsuariosView,
    ObterUsuarioColetivoView,
    ReativarUsuarioView,
    RemoverItemColetivoView,
    SubstituirUsuarioColetivoView,
    BaixarModeloImportacaoUsuariosView,
    PreVisualizarImportacaoUsuariosView,
    ImportarUsuariosLoteView,
    StatusImportacaoLoteView,
    CancelarImportacaoView,
    HistoricoImportacaoLoteView,
)

urlpatterns = [
    path(
        'permissoes/documentacao/',
        DocumentarPermissoesView.as_view(),
        name='permissoes-documentacao',
    ),
    path('usuarios/', roteador_por_metodo(GET=ListarUsuariosView, POST=CriarUsuarioView), name='usuario-list'),
    path('usuarios/<int:pk>/', roteador_por_metodo(GET=DetalheUsuarioView, PATCH=AtualizarUsuarioView), name='usuario-detail'),
    path(
        'usuarios/<int:pk>/coletivo/',
        roteador_por_metodo(GET=ObterUsuarioColetivoView, PUT=SubstituirUsuarioColetivoView),
        name='usuario-coletivo',
    ),
    path(
        'usuarios/<int:pk>/coletivo/itens/',
        AdicionarItemColetivoView.as_view(),
        name='usuario-coletivo-itens',
    ),
    path(
        'usuarios/<int:pk>/coletivo/itens/<str:tipo>/<int:item_id>/',
        RemoverItemColetivoView.as_view(),
        name='usuario-coletivo-item-remover',
    ),
    path('usuarios/<int:pk>/foto-primaria/', AtualizarFotoPrimariaView.as_view(), name='usuario-foto-primaria'),
    path(
        'usuarios/<int:pk>/foto-secundaria/',
        roteador_por_metodo(
            GET=ObterFotoSecundariaView,
            POST=AtualizarFotoSecundariaView,
            DELETE=RemoverFotoSecundariaView,
        ),
        name='usuario-foto-secundaria',
    ),
    path('usuarios/<int:pk>/desativar/', DesativarUsuarioView.as_view(), name='usuario-desativar'),
    path('usuarios/<int:pk>/reativar/', ReativarUsuarioView.as_view(), name='usuario-reativar'),
    path(
        'usuarios/importacao/modelo/',
        BaixarModeloImportacaoUsuariosView.as_view(),
        name='usuarios-importacao-modelo',
    ),
    path(
        'usuarios/importacao/pre-visualizar/',
        PreVisualizarImportacaoUsuariosView.as_view(),
        name='usuarios-importacao-pre-visualizar',
    ),
    path(
        'usuarios/importacao/',
        ImportarUsuariosLoteView.as_view(),
        name='usuarios-importacao',
    ),
    path(
        'usuarios/importacao/status/',
        StatusImportacaoLoteView.as_view(),
        name='usuarios-importacao-status',
    ),
    path(
        'usuarios/importacao/cancelar/',
        CancelarImportacaoView.as_view(),
        name='usuarios-importacao-cancelar',
    ),
    path(
        'usuarios/importacao/historico/',
        HistoricoImportacaoLoteView.as_view(),
        name='usuarios-importacao-historico',
    ),
]
