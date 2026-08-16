'''
Processamento genérico de imagem do Cortex.

Abrir arquivo (com EXIF), recorte central por proporção e reencode JPEG.
Regras específicas de domínio (ex.: retrato 3:4, resolução mínima) ficam no app.
'''
import mimetypes
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from AppCore.core.exceptions.exceptions import ValidationException

TIPOS_IMAGEM_PERMITIDOS = {
    'image/jpeg',
    'image/png',
    'image/webp',
}
FORMATOS_PIL_PERMITIDOS = {'JPEG', 'PNG', 'WEBP'}
MENSAGEM_FORMATO_IMAGEM_NAO_SUPORTADO = (
    'Formato de imagem não suportado. Use JPEG, PNG ou WebP.'
)
EXTENSOES_IMAGEM_PERMITIDAS = {'jpg', 'jpeg', 'png', 'webp'}
TAMANHO_MAXIMO_IMAGEM_BYTES = 3 * 1024 * 1024
QUALIDADE_JPEG = 85
_MAPA_EXTENSAO_CONTENT_TYPE = {
    'image/jpeg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
}


def obter_extensao_imagem(arquivo) -> str:
    '''Infere a extensão permitida a partir do nome ou do content-type.'''
    nome = getattr(arquivo, 'name', '') or ''
    extensao = nome.rsplit('.', 1)[-1].lower() if '.' in nome else ''
    if extensao in EXTENSOES_IMAGEM_PERMITIDAS:
        return 'jpg' if extensao == 'jpeg' else extensao

    content_type = getattr(arquivo, 'content_type', '') or mimetypes.guess_type(nome)[0] or ''
    return _MAPA_EXTENSAO_CONTENT_TYPE.get(content_type, '')


def content_type_por_extensao(extensao: str) -> str:
    '''Resolve o Content-Type HTTP a partir da extensão do arquivo.'''
    content_type = mimetypes.types_map.get(f'.{extensao}', 'application/octet-stream')
    if content_type == 'application/octet-stream' and extensao == 'jpg':
        return 'image/jpeg'
    return content_type


def inspecionar_formato_imagem(arquivo) -> str | None:
    '''
    Abre o arquivo, carrega os pixels e retorna o formato PIL sem converter.
    Reposiciona o cursor do arquivo em 0 para reabertura posterior.
    '''
    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)
    try:
        imagem = Image.open(arquivo)
        imagem.load()
        formato = imagem.format
    except (UnidentifiedImageError, OSError):
        formato = None
    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)
    return formato


def formato_imagem_permitido(arquivo) -> bool:
    '''Indica se o conteúdo real do arquivo é JPEG, PNG ou WebP.'''
    formato = inspecionar_formato_imagem(arquivo)
    return formato in FORMATOS_PIL_PERMITIDOS


def abrir_imagem(arquivo) -> Image.Image:
    '''Abre o arquivo, aplica orientação EXIF e converte para RGB.'''
    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)
    try:
        imagem = Image.open(arquivo)
        imagem.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationException('Arquivo de imagem inválido.') from exc

    if imagem.format not in FORMATOS_PIL_PERMITIDOS:
        raise ValidationException(MENSAGEM_FORMATO_IMAGEM_NAO_SUPORTADO)

    imagem = ImageOps.exif_transpose(imagem) or imagem
    if imagem.mode != 'RGB':
        imagem = imagem.convert('RGB')
    return imagem


def recortar_central(
    imagem: Image.Image,
    proporcao_largura: int,
    proporcao_altura: int,
) -> Image.Image:
    '''
    Recorta o centro da imagem para a proporção informada (largura:altura), sem esticar.
    '''
    largura, altura = imagem.size
    if largura <= 0 or altura <= 0:
        raise ValidationException('Arquivo de imagem inválido.')

    alvo_ratio = proporcao_largura / proporcao_altura
    atual_ratio = largura / altura

    if abs(atual_ratio - alvo_ratio) < 1e-9:
        return imagem

    if atual_ratio > alvo_ratio:
        nova_largura = int(round(altura * alvo_ratio))
        esquerda = (largura - nova_largura) // 2
        caixa = (esquerda, 0, esquerda + nova_largura, altura)
    else:
        nova_altura = int(round(largura / alvo_ratio))
        topo = (altura - nova_altura) // 2
        caixa = (0, topo, largura, topo + nova_altura)

    return imagem.crop(caixa)


def reencode_jpeg(imagem: Image.Image, nome: str = 'foto.jpg') -> BytesIO:
    '''Reencoda a imagem processada em JPEG para upload.'''
    buffer = BytesIO()
    imagem.save(buffer, format='JPEG', quality=QUALIDADE_JPEG)
    buffer.seek(0)
    buffer.name = nome
    return buffer
