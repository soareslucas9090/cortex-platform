import re
from datetime import date, datetime, timedelta, timezone

from rest_framework.test import APITestCase

from AppCore.common.pdf.fontes import obter_fontes

from Infraestrutura.relatorios_emprestimos.dados import (
    DadosRelatorioEmprestimos,
    EmprestimoRelatorio,
    FiltroAplicado,
    ItemRelatorio,
    ResumoRelatorio,
)
from Infraestrutura.relatorios_emprestimos.pdf import renderizar_relatorio_emprestimos


class RenderizadorPdfRelatorioEmprestimosTest(APITestCase):

    def _dados_base(self, emprestimos=None):
        return DadosRelatorioEmprestimos(
            periodo_inicio=date(2026, 3, 1),
            periodo_fim=date(2026, 3, 31),
            emitido_em_rotulo='24/11/2026 10:00',
            emitido_por='Operador Teste',
            escopo='Todas as origens',
            filtros=[
                FiltroAplicado('Solicitante', 'Todos'),
                FiltroAplicado('Entregue por', 'Todos'),
                FiltroAplicado('Tipo de recurso', 'Todos'),
                FiltroAplicado('Bloco', 'Todos'),
                FiltroAplicado('Sala', 'Todas'),
            ],
            resumo=ResumoRelatorio(emprestimos=0, itens=0, devolvidos=0, em_aberto=0, atrasados=0),
            emprestimos=emprestimos or [],
        )

    def test_pdf_vazio(self):
        fontes = obter_fontes()
        self.assertTrue(fontes['fonte_embutida'])
        self.assertNotEqual(fontes['corpo'], 'Helvetica')

        pdf = renderizar_relatorio_emprestimos(self._dados_base())
        self.assertTrue(pdf.startswith(b'%PDF-'))
        self.assertGreater(len(pdf), 500)

    def test_pdf_com_conteudo_rico(self):
        nome_longo = 'ç' + 'ã' * 90 + 'é' * 89
        descricao_longa = 'x' * 85
        agora = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
        itens = [
            ItemRelatorio('CHV-1', descricao_longa, 'Chave', 'Bloco A', 'Sala 1', None, 'Em aberto'),
            ItemRelatorio('CHV-2', 'ok', 'Chave', 'Bloco A', 'Sala 1', agora, 'Devolvido'),
            ItemRelatorio('MID-1', 'mídia', 'Mídia', '', '', agora, 'Devolvido'),
        ]
        emp_a = EmprestimoRelatorio(1, agora, nome_longo, 'Resp', itens)
        emp_b = EmprestimoRelatorio(2, agora - timedelta(hours=1), 'Outro', 'Resp', [
            ItemRelatorio('CHV-9', 'simples', 'Chave', 'B', 'S', None, 'Atrasado'),
        ])
        dados = self._dados_base([emp_a, emp_b])
        dados.resumo = ResumoRelatorio(2, 4, 2, 2, 1)
        pdf = renderizar_relatorio_emprestimos(dados)
        self.assertTrue(pdf.startswith(b'%PDF-'))

    def test_pdf_multipaginas(self):
        agora = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
        emprestimos = []
        for i in range(40):
            dia = agora + timedelta(days=i % 3)
            emprestimos.append(
                EmprestimoRelatorio(
                    i + 1,
                    dia,
                    f'Solicitante {i}',
                    f'Responsável {i}',
                    [
                        ItemRelatorio(f'C{i}a', 'desc', 'Chave', 'Bloco', 'Sala', None, 'Em aberto'),
                        ItemRelatorio(f'C{i}b', 'desc2', 'Mídia', '', '', None, 'Em aberto'),
                    ],
                ),
            )
        dados = self._dados_base(emprestimos)
        dados.resumo = ResumoRelatorio(40, 80, 0, 80, 0)
        pdf = renderizar_relatorio_emprestimos(dados)
        paginas = re.findall(rb'/Type\s*/Page\b(?!s)', pdf)
        self.assertGreaterEqual(len(paginas), 2)

    def test_xml_escape_no_nome(self):
        agora = datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc)
        emp = EmprestimoRelatorio(
            1,
            agora,
            'João <script> & "teste"',
            'Maria > outra',
            [ItemRelatorio('X', 'y', 'Chave', 'B', 'S', None, 'Em aberto')],
        )
        dados = self._dados_base([emp])
        dados.resumo = ResumoRelatorio(1, 1, 0, 1, 0)
        pdf = renderizar_relatorio_emprestimos(dados)
        self.assertTrue(pdf.startswith(b'%PDF-'))