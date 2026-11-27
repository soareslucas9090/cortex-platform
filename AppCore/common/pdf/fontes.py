from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONTES_REGISTRADAS = False
_FONTE_EMBUTIDA = False

DIR_FONTES = Path(__file__).resolve().parent / 'fontes'

NOME_NUNITO = 'MeuIF-Nunito'
NOME_NUNITO_BOLD = 'MeuIF-Nunito-Bold'
NOME_POPPINS = 'MeuIF-Poppins'


def _registrar_ttfont(nome_arquivo: str, nome_interno: str) -> bool:
    caminho = DIR_FONTES / nome_arquivo
    if not caminho.is_file() or caminho.stat().st_size < 1024:
        return False
    try:
        pdfmetrics.registerFont(TTFont(nome_interno, str(caminho)))
        return True
    except Exception:
        return False


def obter_fontes() -> dict:
    global _FONTES_REGISTRADAS, _FONTE_EMBUTIDA
    if _FONTES_REGISTRADAS:
        return _nomes_atuais()

    nunito_ok = _registrar_ttfont('Nunito-Regular.ttf', NOME_NUNITO)
    bold_ok = _registrar_ttfont('Nunito-Bold.ttf', NOME_NUNITO_BOLD)
    poppins_ok = _registrar_ttfont('Poppins-SemiBold.ttf', NOME_POPPINS)

    if nunito_ok and bold_ok:
        try:
            pdfmetrics.registerFontFamily(
                NOME_NUNITO,
                normal=NOME_NUNITO,
                bold=NOME_NUNITO_BOLD,
            )
        except Exception:
            pass

    _FONTE_EMBUTIDA = nunito_ok and bold_ok and poppins_ok

    _FONTES_REGISTRADAS = True
    return {
        'corpo': NOME_NUNITO if nunito_ok else 'Helvetica',
        'corpo_bold': NOME_NUNITO_BOLD if bold_ok else 'Helvetica-Bold',
        'destaque': NOME_POPPINS if poppins_ok else ('Helvetica-Bold' if not nunito_ok else NOME_NUNITO_BOLD),
        'fonte_embutida': _FONTE_EMBUTIDA,
    }


def _nomes_atuais() -> dict:
    nunito_existe = NOME_NUNITO in pdfmetrics.getRegisteredFontNames()
    bold_existe = NOME_NUNITO_BOLD in pdfmetrics.getRegisteredFontNames()
    poppins_existe = NOME_POPPINS in pdfmetrics.getRegisteredFontNames()
    return {
        'corpo': NOME_NUNITO if nunito_existe else 'Helvetica',
        'corpo_bold': NOME_NUNITO_BOLD if bold_existe else 'Helvetica-Bold',
        'destaque': NOME_POPPINS if poppins_existe else 'Helvetica-Bold',
        'fonte_embutida': nunito_existe and bold_existe and poppins_existe,
    }