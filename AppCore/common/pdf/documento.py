from io import BytesIO

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .fontes import NOME_POPPINS, obter_fontes
from .paleta import BRANCO, MUTED, NAVY


ALTURA_FAIXA_CABECALHO = 32
MARGEM_MM = 14
RODAPE_ALTURA = 22


class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        self._titulo = kwargs.pop('titulo_relatorio', 'Relatório')
        self._fontes = kwargs.pop('fontes', obter_fontes())
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for estado in self._saved_page_states:
            self.__dict__.update(estado)
            self._desenhar_faixa_cabecalho()
            self._desenhar_rodape(total)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _desenhar_faixa_cabecalho(self):
        largura, altura = self._pagesize
        self.saveState()
        self.setFillColor(NAVY)
        self.rect(0, altura - ALTURA_FAIXA_CABECALHO, largura, ALTURA_FAIXA_CABECALHO, fill=1, stroke=0)
        self.setFillColor(BRANCO)
        destaque = self._fontes['destaque']
        self.setFont(destaque, 11)
        self.drawString(MARGEM_MM * mm, altura - ALTURA_FAIXA_CABECALHO + 10, self._titulo)
        largura_meuif = self.stringWidth('MeuIF', destaque, 11)
        self.drawString(largura - MARGEM_MM * mm - largura_meuif, altura - ALTURA_FAIXA_CABECALHO + 10, 'MeuIF')
        self.restoreState()

    def _desenhar_rodape(self, total_paginas: int):
        largura, _altura = self._pagesize
        self.saveState()
        y_base = 10
        self.setFillColor(MUTED)
        corpo = self._fontes['corpo']
        self.setFont(corpo, 7)
        texto_pagina = f'Página {self._pageNumber} de {total_paginas}'
        largura_texto = self.stringWidth(texto_pagina, corpo, 7)
        self.drawString((largura - largura_texto) / 2, y_base + 8, texto_pagina)
        aviso = 'Documento gerado para consulta. Não armazenado.'
        self.drawString((largura - self.stringWidth(aviso, corpo, 7)) / 2, y_base, aviso)
        self.restoreState()


def criar_doc_template(buffer: BytesIO, titulo: str):
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

    fontes = obter_fontes()
    pagina = landscape(A4)
    largura, altura = pagina
    margem = MARGEM_MM * mm
    topo_conteudo = altura - margem - ALTURA_FAIXA_CABECALHO - 4
    base_conteudo = margem + RODAPE_ALTURA

    quadro = Frame(
        margem,
        base_conteudo,
        largura - 2 * margem,
        topo_conteudo - base_conteudo,
        id='conteudo',
        showBoundary=0,
    )

    def ao_desenhar_pagina(can, _doc):
        if isinstance(can, NumberedCanvas):
            can._desenhar_faixa_cabecalho()

    doc = BaseDocTemplate(
        buffer,
        pagesize=pagina,
        title=titulo,
        leftMargin=margem,
        rightMargin=margem,
        topMargin=topo_conteudo,
        bottomMargin=base_conteudo,
    )
    modelo = PageTemplate(id='principal', frames=[quadro], onPage=ao_desenhar_pagina)
    doc.addPageTemplates([modelo])

    class CanvasNumerado(NumberedCanvas):
        def __init__(self, *args, **kwargs):
            kwargs['titulo_relatorio'] = titulo
            kwargs['fontes'] = fontes
            super().__init__(*args, **kwargs)

    return doc, fontes, CanvasNumerado