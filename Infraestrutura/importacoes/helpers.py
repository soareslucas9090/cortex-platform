import requests
from django.core.files.uploadedfile import SimpleUploadedFile

from AppCore.common.storage.imagens import TAMANHO_MAXIMO_IMAGEM_BYTES


def obter_bloco_por_id_planilha(bloco_id_planilha: int, mapa_blocos: dict):
    """Resolve o bloco real a partir do identificador temporário da planilha."""
    return mapa_blocos.get(bloco_id_planilha)


def obter_sala_por_id_planilha(sala_id_planilha: int, mapa_salas: dict):
    """Resolve a sala real a partir do identificador temporário da planilha."""
    return mapa_salas.get(sala_id_planilha)


def baixar_imagem_de_url(url: str, timeout: int = 30):
    """Baixa uma imagem de URL HTTP(S) e retorna um arquivo pronto para upload."""
    if not url:
        raise ValueError('URL da foto não informada.')

    resposta = requests.get(url, timeout=timeout, stream=True)
    resposta.raise_for_status()

    content_type = resposta.headers.get('Content-Type', 'image/jpeg')
    if ';' in content_type:
        content_type = content_type.split(';')[0].strip()

    conteudo = b''
    for chunk in resposta.iter_content(chunk_size=8192):
        if not chunk:
            continue
        conteudo += chunk
        if len(conteudo) > TAMANHO_MAXIMO_IMAGEM_BYTES:
            raise ValueError('A imagem excede o tamanho máximo de 3 MB.')

    if not conteudo:
        raise ValueError('A URL da foto não retornou conteúdo.')

    extensao = 'jpg'
    if 'png' in content_type:
        extensao = 'png'
    elif 'webp' in content_type:
        extensao = 'webp'

    nome_arquivo = f'importacao-foto.{extensao}'
    return SimpleUploadedFile(
        name=nome_arquivo,
        content=conteudo,
        content_type=content_type,
    )
