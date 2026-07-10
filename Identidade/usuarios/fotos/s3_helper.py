import logging
import mimetypes
import uuid
from collections.abc import Iterator
from urllib.parse import urlparse

from botocore.exceptions import ClientError
from django.conf import settings
from django.urls import reverse

from Identidade.usuarios.importacao.s3_helper import _get_s3_client

logger = logging.getLogger(__name__)

TIPOS_IMAGEM_PERMITIDOS = {
    'image/jpeg',
    'image/png',
    'image/webp',
}
EXTENSOES_PERMITIDAS = {'jpg', 'jpeg', 'png', 'webp'}
TAMANHO_MAXIMO_FOTO_SECUNDARIA_BYTES = 3 * 1024 * 1024
PREFIXO_S3_FOTO_SECUNDARIA = 'Cortex/usuarios/fotos'


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


def normalizar_s3_key(valor: str | None) -> str | None:
    """
    Aceita chave S3 pura ou URL e retorna a chave do objeto.
    """
    if not valor:
        return None

    valor = valor.strip()
    if not valor.startswith(('http://', 'https://')):
        return valor

    parsed = urlparse(valor)
    if not parsed.path:
        return None

    path = parsed.path.lstrip('/')
    if path.startswith(f'{PREFIXO_S3_FOTO_SECUNDARIA}/'):
        return path

    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
    if bucket_name and path.startswith(f'{bucket_name}/{PREFIXO_S3_FOTO_SECUNDARIA}/'):
        return path[len(bucket_name) + 1:]

    return path


def montar_url_proxy_foto_secundaria(
    usuario_id: int,
    s3_key: str | None,
    request=None,
) -> str | None:
    """
    Monta a URL pública do proxy da API para a foto secundária do usuário.
    Inclui parâmetro de versão para invalidar cache após novo upload.
    """
    if not s3_key:
        return None

    if request is not None:
        base_url = request.build_absolute_uri(
            reverse('identidade:usuario-foto-secundaria', kwargs={'pk': usuario_id})
        )
    else:
        public_base = getattr(settings, 'CORTEX_PUBLIC_BASE_URL', '').rstrip('/')
        if not public_base:
            return None
        base_url = f'{public_base}/cortex/identidade/usuarios/{usuario_id}/foto-secundaria/'

    # cache bust: uuid do arquivo na chave S3
    nome_arquivo = s3_key.rsplit('/', 1)[-1]
    versao = nome_arquivo.rsplit('.', 1)[0]
    return f'{base_url}?v={versao}'


def upload_foto_secundaria(usuario_id: int, arquivo) -> str:
    """
    Envia a foto secundária para o bucket S3 e retorna a chave do objeto.
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

    s3_key = f'{PREFIXO_S3_FOTO_SECUNDARIA}/{usuario_id}/{uuid.uuid4().hex}.{extensao}'

    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)

    extra_args = {'ContentType': content_type}
    s3_client.upload_fileobj(arquivo, bucket_name, s3_key, ExtraArgs=extra_args)

    return s3_key


def iterar_foto_secundaria_do_s3(s3_key: str) -> tuple[Iterator[bytes], str]:
    """
    Obtém o stream e o content-type da foto secundária no S3.
    """
    s3_client, bucket_name = _get_s3_client()
    if not s3_client:
        raise ValueError('Configuração de armazenamento S3 inválida.')

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    except ClientError as exc:
        logger.warning('Foto secundária não encontrada no S3 (%s): %s', s3_key, exc)
        raise

    body = response['Body']
    content_type = (
        response.get('ContentType')
        or mimetypes.guess_type(s3_key)[0]
        or 'application/octet-stream'
    )

    def _iterar_chunks():
        try:
            yield from body.iter_chunks()
        finally:
            body.close()

    return _iterar_chunks(), content_type


def remover_foto_secundaria_do_s3(valor: str) -> None:
    """
    Remove a foto secundária do S3 de forma best-effort.
    Falhas são registradas em log e não interrompem a operação no banco.
    """
    s3_key = normalizar_s3_key(valor)
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
