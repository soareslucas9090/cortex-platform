import logging
import mimetypes
import uuid
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from django.conf import settings

from Identidade.usuarios.importacao.s3_helper import _get_s3_client

logger = logging.getLogger(__name__)

TIPOS_IMAGEM_PERMITIDOS = {
    'image/jpeg',
    'image/png',
    'image/webp',
}
EXTENSOES_PERMITIDAS = {'jpg', 'jpeg', 'png', 'webp'}
TAMANHO_MAXIMO_FOTO_SECUNDARIA_BYTES = 3 * 1024 * 1024


def _obter_extensao(arquivo) -> str:
    nome = getattr(arquivo, 'name', '') or ''
    extensao = nome.rsplit('.', 1)[-1].lower() if '.' in nome else ''
    if extensao in EXTENSOES_PERMITIDAS:
        return 'jpg' if extensao == 'jpeg' else extensao

    content_type = getattr(arquivo, 'content_type', '') or mimetypes.guess_type(nome)[0] or ''
    mapa = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
    }
    return mapa.get(content_type, '')


def _montar_url_publica(s3_key: str) -> str:
    base_url = getattr(settings, 'AWS_S3_PUBLIC_BASE_URL', '')
    if not base_url:
        raise ValueError('AWS_S3_PUBLIC_BASE_URL não configurada.')
    return f'{base_url}/{s3_key}'


def _extrair_s3_key_da_url(url: str) -> str | None:
    if not url:
        return None

    base_url = getattr(settings, 'AWS_S3_PUBLIC_BASE_URL', '').rstrip('/')
    if base_url and url.startswith(base_url + '/'):
        return url[len(base_url) + 1:]

    parsed = urlparse(url)
    if not parsed.path:
        return None
    return parsed.path.lstrip('/')


def upload_foto_secundaria(usuario_id: int, arquivo) -> str:
    """
    Envia a foto secundária para o bucket S3 e retorna a URL pública.
    """
    s3_client, bucket_name = _get_s3_client()
    if not s3_client:
        raise ValueError('Configuração de armazenamento S3 inválida.')

    extensao = _obter_extensao(arquivo)
    if not extensao:
        raise ValueError('Formato de imagem não suportado. Use JPEG, PNG ou WebP.')

    content_type = mimetypes.types_map.get(f'.{extensao}', 'application/octet-stream')
    if content_type == 'application/octet-stream' and extensao == 'jpg':
        content_type = 'image/jpeg'

    s3_key = f'Cortex/usuarios/fotos/{usuario_id}/{uuid.uuid4().hex}.{extensao}'

    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)

    extra_args = {'ContentType': content_type}
    s3_client.upload_fileobj(arquivo, bucket_name, s3_key, ExtraArgs=extra_args)

    return _montar_url_publica(s3_key)


def remover_foto_secundaria_do_s3(url: str) -> None:
    """
    Remove a foto secundária do S3 de forma best-effort.
    Falhas são registradas em log e não interrompem a operação no banco.
    """
    s3_key = _extrair_s3_key_da_url(url)
    if not s3_key:
        return

    s3_client, bucket_name = _get_s3_client()
    if not s3_client:
        logger.warning('Não foi possível remover foto do S3: cliente não configurado.')
        return

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info('Foto secundária removida do S3: %s', s3_key)
    except ClientError as exc:
        logger.warning('Erro ao remover foto secundária do S3 (%s): %s', s3_key, exc)
    except Exception as exc:
        logger.warning('Erro inesperado ao remover foto secundária do S3 (%s): %s', s3_key, exc)
