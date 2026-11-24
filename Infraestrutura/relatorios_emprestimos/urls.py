from django.urls import path

from .views import BaixarRelatorioEmprestimosPdfView, ListarPessoasRelatorioView

urlpatterns = [
    path(
        'emprestimos/relatorio/pdf/',
        BaixarRelatorioEmprestimosPdfView.as_view(),
        name='emprestimos-relatorio-pdf',
    ),
    path(
        'emprestimos/relatorio/pessoas/',
        ListarPessoasRelatorioView.as_view(),
        name='emprestimos-relatorio-pessoas',
    ),
]