import time
from urllib.parse import urlparse

import requests
from django.core.files.uploadedfile import SimpleUploadedFile

from AppCore.common.storage.imagens import TAMANHO_MAXIMO_IMAGEM_BYTES

TENTATIVAS_DOWNLOAD_IMAGEM = 4
ESPERA_MAXIMA_RETRY_SEGUNDOS = 15
STATUS_HTTP_RETRY = {429, 500, 502, 503, 504}
HEADERS_DOWNLOAD_IMAGEM = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'image/avif,image/webp,image/apng,image/jpeg,image/png,image/*,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
}


def obter_bloco_por_id_planilha(bloco_id_planilha: int, mapa_blocos: dict):
    """Resolve o bloco real a partir do identificador temporário da planilha."""
    return mapa_blocos.get(bloco_id_planilha)


def obter_sala_por_id_planilha(sala_id_planilha: int, mapa_salas: dict):
    """Resolve a sala real a partir do identificador temporário da planilha."""
    return mapa_salas.get(sala_id_planilha)


def _headers_download(url: str) -> dict:
    headers = dict(HEADERS_DOWNLOAD_IMAGEM)
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        headers['Referer'] = f'{parsed.scheme}://{parsed.netloc}/'
    return headers


def _espera_retry(resposta, tentativa: int) -> float:
    retry_after = resposta.headers.get('Retry-After')
    if retry_after:
        try:
            espera = float(retry_after)
            if espera > 0:
                return min(espera, ESPERA_MAXIMA_RETRY_SEGUNDOS)
        except (TypeError, ValueError):
            pass
    return min(2 ** tentativa, ESPERA_MAXIMA_RETRY_SEGUNDOS)


def _mensagem_erro_http(status_code: int) -> str:
    if status_code == 429:
        return (
            'O servidor da imagem recusou o download por excesso de requisições '
            '(HTTP 429). Tente novamente mais tarde ou use outra URL.'
        )
    if status_code == 403:
        return 'O servidor da imagem recusou o acesso à foto (HTTP 403).'
    if status_code == 404:
        return 'A foto não foi encontrada na URL informada (HTTP 404).'
    return f'Não foi possível baixar a foto (HTTP {status_code}).'


def baixar_imagem_de_url(url: str, timeout: int = 30):
    """Baixa uma imagem de URL HTTP(S) e retorna um arquivo pronto para upload."""
    if not url:
        raise ValueError('URL da foto não informada.')

    headers = _headers_download(url)
    resposta = None
    try:
        for tentativa in range(1, TENTATIVAS_DOWNLOAD_IMAGEM + 1):
            try:
                resposta = requests.get(
                    url,
                    timeout=timeout,
                    stream=True,
                    headers=headers,
                )
            except requests.RequestException as exc:
                raise ValueError(
                    'Não foi possível baixar a foto da URL informada.'
                ) from exc

            if (
                resposta.status_code in STATUS_HTTP_RETRY
                and tentativa < TENTATIVAS_DOWNLOAD_IMAGEM
            ):
                espera = _espera_retry(resposta, tentativa)
                resposta.close()
                time.sleep(espera)
                continue
            break

        if not resposta.ok:
            raise ValueError(_mensagem_erro_http(resposta.status_code))

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
    finally:
        if resposta is not None:
            resposta.close()

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
