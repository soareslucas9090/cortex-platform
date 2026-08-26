import os
import logging

from botocore.exceptions import ClientError

from AppCore.common.storage.s3 import obter_cliente_s3

logger = logging.getLogger(__name__)


def _get_s3_client():
    return obter_cliente_s3()


def upload_importacao_to_s3(importacao_lote):
    """
    Realiza o upload do arquivo da importacao para o bucket S3
    para que o worker em outra maquina/container possa baixa-lo.
    """
    s3_client, bucket_name = _get_s3_client()
    if not s3_client:
        return False

    try:
        s3_key = f"Cortex/media/{importacao_lote.arquivo.name}"

        file_path = importacao_lote.arquivo.path
        if not os.path.exists(file_path):
            logger.error('Arquivo local %s nao existe para upload.', file_path)
            return False

        with open(file_path, 'rb') as f:
            s3_client.upload_fileobj(f, bucket_name, s3_key)

        logger.info('Arquivo %s enviado com sucesso para o S3: %s', file_path, s3_key)
        return True
    except Exception as e:
        logger.error('Erro ao realizar upload da importacao para S3: %s', e)
        return False


def download_importacao_from_s3_if_needed(importacao_lote):
    """
    Verifica se o arquivo da importacao existe localmente.
    Se nao existir, tenta baixa-lo do bucket S3.
    """
    file_path = importacao_lote.arquivo.path

    if os.path.exists(file_path):
        return True

    logger.info('Arquivo local %s nao encontrado. Tentando baixar do S3...', file_path)

    s3_client, bucket_name = _get_s3_client()
    if not s3_client:
        return False

    try:
        s3_key = f"Cortex/media/{importacao_lote.arquivo.name}"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            s3_client.download_fileobj(bucket_name, s3_key, f)

        logger.info('Arquivo baixado do S3 com sucesso para %s', file_path)
        return True
    except ClientError as e:
        logger.error('Erro de S3 ao baixar o arquivo %s: %s', s3_key, e)
        return False
    except Exception as e:
        logger.error('Erro inesperado ao baixar arquivo do S3 para %s: %s', file_path, e)
        return False
