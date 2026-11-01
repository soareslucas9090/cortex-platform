from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import (
    DetalharEventoAcessoView,
    ListarAlunosEventoAcessoView,
    ListarEventosAcessoView,
    ListarResponsaveisElegiveisView,
    RegistrarEventoAcessoView,
)

urlpatterns = [
    path(
        "eventos/",
        roteador_por_metodo(GET=ListarEventosAcessoView),
        name="evento-acesso-list",
    ),
    path(
        "eventos/responsaveis-elegiveis/",
        roteador_por_metodo(GET=ListarResponsaveisElegiveisView),
        name="evento-acesso-responsaveis",
    ),
    path(
        "eventos/<uuid:grupo_portaria_id>/",
        roteador_por_metodo(GET=DetalharEventoAcessoView),
        name="evento-acesso-detail",
    ),
    path(
        "eventos/<uuid:grupo_portaria_id>/alunos/",
        roteador_por_metodo(GET=ListarAlunosEventoAcessoView),
        name="evento-acesso-alunos",
    ),
    path(
        "eventos/<uuid:grupo_portaria_id>/registrar/",
        roteador_por_metodo(POST=RegistrarEventoAcessoView),
        name="evento-acesso-registrar",
    ),
]
