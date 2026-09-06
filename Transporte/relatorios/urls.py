from django.urls import path

from AppCore.basics.views.basic_views import roteador_por_metodo

from .views import RelatorioAlunosDashboardView, RelatorioAlunosDetalhesView

urlpatterns = [
    path(
        'relatorio-alunos/dashboard/',
        roteador_por_metodo(GET=RelatorioAlunosDashboardView),
        name='relatorio-alunos-dashboard',
    ),
    path(
        'relatorio-alunos/detalhes/',
        roteador_por_metodo(GET=RelatorioAlunosDetalhesView),
        name='relatorio-alunos-detalhes',
    ),
]
