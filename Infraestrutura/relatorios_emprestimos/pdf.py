from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from AppCore.common.pdf.documento import criar_doc_template
from AppCore.common.pdf.paleta import (
    AMBAR_TEXTO,
    BORDA,
    BRANCO,
    FUNDO,
    INK,
    MUTED,
    NAVY,
    SAGE,
    VERDE_TEXTO,
    ZEBRA,
)

from Infraestrutura.emprestimos.helpers import FUSO_HORARIO_EMPRESTIMOS

from .constantes import MESES_PT
from .dados import DadosRelatorioEmprestimos

LARGURAS_COLUNAS = [26, 68, 108, 104, 132, 62, 90, 68, 104]

TITULO_DOCUMENTO = 'Relatório de empréstimos'


def renderizar_relatorio_emprestimos(dados: DadosRelatorioEmprestimos) -> bytes:
    buffer = BytesIO()
    doc, fontes, canvas_maker = criar_doc_template(buffer, TITULO_DOCUMENTO)
    estilos = _criar_estilos(fontes)

    historia = []
    historia.extend(_bloco_metadados(dados, estilos))
    historia.append(Spacer(1, 6))
    historia.extend(_bloco_filtros(dados, estilos))
    historia.append(Spacer(1, 8))
    historia.extend(_bloco_resumo(dados, estilos))
    historia.append(Spacer(1, 10))

    if dados.emprestimos:
        historia.append(_montar_tabela_principal(dados, estilos))
    else:
        historia.append(_caixa_vazio(estilos))

    doc.build(historia, canvasmaker=canvas_maker)
    return buffer.getvalue()


def _criar_estilos(fontes: dict) -> dict:
    corpo = fontes['corpo']
    corpo_bold = fontes['corpo_bold']
    base = ParagraphStyle(
        'corpo',
        fontName=corpo,
        fontSize=8,
        leading=10.5,
        textColor=INK,
        alignment=TA_LEFT,
        wordWrap='CJK',
    )
    return {
        'corpo': base,
        'corpo_central': ParagraphStyle('corpo_central', parent=base, alignment=TA_CENTER),
        'corpo_muted': ParagraphStyle('corpo_muted', parent=base, textColor=MUTED),
        'corpo_bold': ParagraphStyle('corpo_bold', parent=base, fontName=corpo_bold),
        'cabecalho_celula': ParagraphStyle(
            'cabecalho_celula',
            parent=base,
            fontName=corpo_bold,
            textColor=BRANCO,
            fontSize=7.5,
            alignment=TA_CENTER,
        ),
        'situacao_devolvido': ParagraphStyle('sit_dev', parent=base, textColor=VERDE_TEXTO),
        'situacao_aberto': ParagraphStyle('sit_aberto', parent=base, textColor=INK),
        'situacao_atrasado': ParagraphStyle('sit_atr', parent=base, textColor=AMBAR_TEXTO),
        'resumo_numero': ParagraphStyle(
            'resumo_num',
            parent=base,
            fontName=corpo_bold,
            fontSize=14,
            alignment=TA_CENTER,
        ),
        'resumo_rotulo': ParagraphStyle(
            'resumo_rot',
            parent=base,
            fontSize=7.5,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
        'dia_separador': ParagraphStyle(
            'dia_sep',
            parent=base,
            fontName=corpo_bold,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        'vazio': ParagraphStyle('vazio', parent=base, alignment=TA_CENTER),
    }


def _p(texto: str, estilo) -> Paragraph:
    return Paragraph(escape(texto), estilo)


def _formatar_data_hora_sp(valor) -> str:
    if valor is None:
        return '-'
    local = valor.astimezone(FUSO_HORARIO_EMPRESTIMOS)
    return local.strftime('%d/%m/%Y %H:%M')


def _data_local_sp(valor):
    return valor.astimezone(FUSO_HORARIO_EMPRESTIMOS).date()


def _rotulo_dia_extenso(dia) -> str:
    return f'{dia.day} de {MESES_PT[dia.month - 1]} de {dia.year}'


def _bloco_metadados(dados: DadosRelatorioEmprestimos, estilos: dict) -> list:
    dias = (dados.periodo_fim - dados.periodo_inicio).days + 1
    inicio = dados.periodo_inicio.strftime('%d/%m/%Y')
    fim = dados.periodo_fim.strftime('%d/%m/%Y')
    linhas = [
        _p(
            f'Período: {inicio} a {fim} ({dias} dias)  |  Emitido em: {dados.emitido_em_rotulo}  |  '
            f'Emitido por: {dados.emitido_por}  |  Escopo: {dados.escopo}',
            estilos['corpo'],
        ),
    ]
    return linhas


def _bloco_filtros(dados: DadosRelatorioEmprestimos, estilos: dict) -> list:
    largura = sum(LARGURAS_COLUNAS)
    linhas_tabela = [[_p('Filtros aplicados', estilos['corpo_bold']), _p('', estilos['corpo'])]]
    for filtro in dados.filtros:
        linhas_tabela.append([
            _p(filtro.rotulo, estilos['corpo_muted']),
            _p(filtro.valor, estilos['corpo']),
        ])
    tabela = Table(linhas_tabela, colWidths=[140, largura - 140])
    tabela.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), FUNDO),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDA),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDA),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('SPAN', (0, 0), (1, 0)),
        ]),
    )
    return [tabela]


def _bloco_resumo(dados: DadosRelatorioEmprestimos, estilos: dict) -> list:
    resumo = dados.resumo
    celulas = [
        [
            _p(str(resumo.emprestimos), estilos['resumo_numero']),
            _p(str(resumo.itens), estilos['resumo_numero']),
            _p(str(resumo.devolvidos), estilos['resumo_numero']),
            _p(str(resumo.em_aberto), estilos['resumo_numero']),
        ],
        [
            _p('Empréstimos', estilos['resumo_rotulo']),
            _p('Itens', estilos['resumo_rotulo']),
            _p('Devolvidos', estilos['resumo_rotulo']),
            _p('Em aberto', estilos['resumo_rotulo']),
        ],
    ]
    celulas[1][3] = Paragraph(
        escape('Em aberto') + f'<br/>{escape(str(resumo.atrasados))} atrasados',
        estilos['resumo_rotulo'],
    )
    largura = sum(LARGURAS_COLUNAS)
    col_w = largura / 4
    tabela = Table(celulas, colWidths=[col_w] * 4)
    tabela.setStyle(
        TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), SAGE),
            ('BOX', (0, 0), (-1, -1), 0.5, BORDA),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, BORDA),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]),
    )
    return [tabela]


def _caixa_vazio(estilos: dict) -> Table:
    texto = _p(
        'Nenhum empréstimo encontrado para os filtros informados.',
        estilos['vazio'],
    )
    tabela = Table([[texto]], colWidths=[sum(LARGURAS_COLUNAS)])
    tabela.setStyle(
        TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, BORDA),
            ('TOPPADDING', (0, 0), (-1, -1), 16),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 16),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]),
    )
    return tabela


def _estilo_situacao(situacao: str, estilos: dict):
    if situacao == 'Devolvido':
        return estilos['situacao_devolvido']
    if situacao == 'Atrasado':
        return estilos['situacao_atrasado']
    return estilos['situacao_aberto']


def _montar_tabela_principal(dados: DadosRelatorioEmprestimos, estilos: dict) -> Table:
    cabecalho = [
        _p('Nº', estilos['cabecalho_celula']),
        _p('Retirada', estilos['cabecalho_celula']),
        _p('Solicitante', estilos['cabecalho_celula']),
        _p('Entregue por', estilos['cabecalho_celula']),
        _p('Recurso', estilos['cabecalho_celula']),
        _p('Tipo', estilos['cabecalho_celula']),
        _p('Local', estilos['cabecalho_celula']),
        _p('Devolução', estilos['cabecalho_celula']),
        _p('Situação', estilos['cabecalho_celula']),
    ]
    linhas = [cabecalho]
    estilos_zebra: list[tuple] = []
    indice_linha = 1
    indice_emprestimo = 0
    dia_anterior = None
    num_colunas = len(LARGURAS_COLUNAS)

    for emprestimo in dados.emprestimos:
        dia_atual = _data_local_sp(emprestimo.retirada_em)
        if dia_anterior is not None and dia_atual != dia_anterior:
            separador = _p(_rotulo_dia_extenso(dia_atual), estilos['dia_separador'])
            linhas.append([separador] + [''] * (num_colunas - 1))
            estilos_zebra.append(('BACKGROUND', (0, indice_linha), (-1, indice_linha), SAGE))
            estilos_zebra.append(('SPAN', (0, indice_linha), (-1, indice_linha)))
            estilos_zebra.append(('TOPPADDING', (0, indice_linha), (-1, indice_linha), 5))
            estilos_zebra.append(('BOTTOMPADDING', (0, indice_linha), (-1, indice_linha), 5))
            indice_linha += 1
        elif dia_anterior is None:
            separador = _p(_rotulo_dia_extenso(dia_atual), estilos['dia_separador'])
            linhas.append([separador] + [''] * (num_colunas - 1))
            estilos_zebra.append(('BACKGROUND', (0, indice_linha), (-1, indice_linha), SAGE))
            estilos_zebra.append(('SPAN', (0, indice_linha), (-1, indice_linha)))
            indice_linha += 1

        dia_anterior = dia_atual
        fundo_zebra = ZEBRA if indice_emprestimo % 2 else colors.white

        itens = emprestimo.itens or [None]
        for pos, item in enumerate(itens):
            if item is None:
                continue
            local = 'Sem sala'
            if item.bloco or item.sala:
                if item.bloco and item.sala:
                    local = f'{item.bloco} - {item.sala}'
                elif item.bloco:
                    local = item.bloco
                else:
                    local = item.sala

            recurso_html = (
                f'<b>{escape(item.codigo)}</b><br/>{escape(item.descricao)}'
            )
            cel_recursos = Paragraph(recurso_html, estilos['corpo'])
            sit_estilo = _estilo_situacao(item.situacao, estilos)

            if pos == 0:
                linha = [
                    _p(str(emprestimo.numero), estilos['corpo']),
                    _p(_formatar_data_hora_sp(emprestimo.retirada_em), estilos['corpo']),
                    _p(emprestimo.solicitante, estilos['corpo']),
                    _p(emprestimo.responsavel, estilos['corpo']),
                    cel_recursos,
                    _p(item.tipo_rotulo, estilos['corpo']),
                    _p(local, estilos['corpo']),
                    _p(_formatar_data_hora_sp(item.devolvido_em), estilos['corpo']),
                    _p(item.situacao, sit_estilo),
                ]
            else:
                linha = [
                    _p('', estilos['corpo']),
                    _p('', estilos['corpo']),
                    _p('', estilos['corpo']),
                    _p('', estilos['corpo']),
                    cel_recursos,
                    _p(item.tipo_rotulo, estilos['corpo']),
                    _p(local, estilos['corpo']),
                    _p(_formatar_data_hora_sp(item.devolvido_em), estilos['corpo']),
                    _p(item.situacao, sit_estilo),
                ]

            linhas.append(linha)
            estilos_zebra.append(('BACKGROUND', (0, indice_linha), (-1, indice_linha), fundo_zebra))
            indice_linha += 1

        indice_emprestimo += 1

    tabela = Table(linhas, colWidths=LARGURAS_COLUNAS, repeatRows=1)
    estilo_base = [
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), BRANCO),
        ('GRID', (0, 0), (-1, -1), 0.25, BORDA),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]
    estilo_base.extend(estilos_zebra)
    tabela.setStyle(TableStyle(estilo_base))
    return tabela