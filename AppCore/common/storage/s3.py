'''
Armazenamento S3 compartilhado do Cortex.

Use este módulo em qualquer domínio que envie, leia ou remova objetos no bucket
do projeto. Não copie helpers S3 para dentro dos apps.
'''
import logging
import mimetypes
import uuid
from collections.abc import Iterator
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.urls import reverse

from .imagens import content_type_por_extensao, obter_extensao_imagem

logger = logging.getLogger(__name__)


def obter_cliente_s3():
    '''
    Instancia o cliente S3 a partir das settings do projeto.
    Retorna (cliente, bucket) ou (None, None) se a configuração estiver incompleta.
    '''
    endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)

    if not all([endpoint_url, bucket_name, access_key, secret_key]):
        logger.error('Credenciais de S3 do projeto não configuradas completamente.')
        return None, None

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
        )
        return s3_client, bucket_name
    except Exception as exc:
        logger.error('Erro ao instanciar cliente S3: %s', exc)
        return None, None


def normalizar_chave_s3(valor: str | None, prefixo: str | None = None) -> str | None:
    '''
    Aceita chave S3 pura ou URL e retorna a chave do objeto.
    Se ``prefixo`` for informado, remove o bucket quando ele aparecer no path.
    '''
    if not valor:
        return None

    valor = valor.strip()
    if not valor.startswith(('http://', 'https://')):
        return valor

    parsed = urlparse(valor)
    if not parsed.path:
        return None

    path = parsed.path.lstrip('/')
    if prefixo and path.startswith(f'{prefixo}/'):
        return path

    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
    if prefixo and bucket_name and path.startswith(f'{bucket_name}/{prefixo}/'):
        return path[len(bucket_name) + 1:]

    return path


def montar_url_proxy_arquivo(
    objeto_id: int,
    s3_key: str | None,
    nome_url: str,
    request=None,
    *,
    caminho_fallback: str | None = None,
) -> str | None:
    '''
    Monta a URL pública do proxy da API para um arquivo no S3.
    Inclui ``?v=`` com o identificador do arquivo para invalidar cache após novo upload.
    '''
    if not s3_key:
        return None

    if request is not None:
        base_url = request.build_absolute_uri(
            reverse(nome_url, kwargs={'pk': objeto_id})
        )
    else:
        public_base = getattr(settings, 'CORTEX_PUBLIC_BASE_URL', '').rstrip('/')
        if not public_base or not caminho_fallback:
            return None
        base_url = f'{public_base}{caminho_fallback}'

    nome_arquivo = s3_key.rsplit('/', 1)[-1]
    versao = nome_arquivo.rsplit('.', 1)[0]
    return f'{base_url}?v={versao}'


def enviar_arquivo_s3(
    prefixo: str,
    objeto_id: int,
    arquivo,
    *,
    extensao: str | None = None,
    content_type: str | None = None,
) -> str:
    '''
    Envia o arquivo para o bucket e retorna a chave do objeto.
    A chave segue ``{prefixo}/{objeto_id}/{uuid}.{extensao}``.
    '''
    s3_client, bucket_name = obter_cliente_s3()
    if not s3_client:
        raise ValueError('Configuração de armazenamento S3 inválida.')

    extensao = extensao or obter_extensao_imagem(arquivo)
    if not extensao:
        raise ValueError('Formato de imagem não suportado. Use JPEG, PNG ou WebP.')

    content_type = content_type or content_type_por_extensao(extensao)
    s3_key = f'{prefixo}/{objeto_id}/{uuid.uuid4().hex}.{extensao}'

    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)

    s3_client.upload_fileobj(arquivo, bucket_name, s3_key, ExtraArgs={'ContentType': content_type})
    return s3_key


def iterar_objeto_s3(
    s3_key: str,
    content_type_padrao: str = 'application/octet-stream',
) -> tuple[Iterator[bytes], str]:
    '''Obtém o stream e o content-type de um objeto no S3.'''
    s3_client, bucket_name = obter_cliente_s3()
    if not s3_client:
        raise ValueError('Configuração de armazenamento S3 inválida.')

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    except ClientError as exc:
        logger.warning('Objeto não encontrado no S3 (%s): %s', s3_key, exc)
        raise

    body = response['Body']
    content_type = (
        response.get('ContentType')
        or mimetypes.guess_type(s3_key)[0]
        or content_type_padrao
    )

    def _iterar_chunks():
        try:
            yield from body.iter_chunks()
        finally:
            body.close()

    return _iterar_chunks(), content_type


def remover_objeto_s3(valor: str, prefixo: str | None = None) -> None:
    '''
    Remove o objeto no S3 de forma best-effort.
    Falhas são registradas em log e não interrompem a operação no banco.
    '''
    s3_key = normalizar_chave_s3(valor, prefixo=prefixo)
    if not s3_key:
        return

    s3_client, bucket_name = obter_cliente_s3()
    if not s3_client:
        logger.warning('Não foi possível remover objeto do S3: cliente não configurado.')
        return

    try:
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        logger.info('Objeto removido do S3: %s', s3_key)
    except ClientError as exc:
        logger.warning('Erro ao remover objeto do S3 (%s): %s', s3_key, exc)
    except Exception as exc:
        logger.warning('Erro inesperado ao remover objeto do S3 (%s): %s', s3_key, exc)
