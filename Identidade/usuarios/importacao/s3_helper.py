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
        # Pega a path relativa dentro de media para usar como S3 Key
        s3_key = f"Cortex/media/{importacao_lote.arquivo.name}"
        
        # Abre o arquivo local e faz o upload
        file_path = importacao_lote.arquivo.path
        if not os.path.exists(file_path):
            logger.error(f"Arquivo local {file_path} nao existe para upload.")
            return False

        with open(file_path, 'rb') as f:
            s3_client.upload_fileobj(f, bucket_name, s3_key)
        
        logger.info(f"Arquivo {file_path} enviado com sucesso para o S3: {s3_key}")
        return True
    except Exception as e:
        logger.error(f"Erro ao realizar upload da importacao para S3: {e}")
        return False

def download_importacao_from_s3_if_needed(importacao_lote):
    """
    Verifica se o arquivo da importacao existe localmente.
    Se nao existir (ex: worker em container separado sem compartilhamento),
    tenta baixa-lo do bucket S3.
    """
    file_path = importacao_lote.arquivo.path
    
    if os.path.exists(file_path):
        # Ja existe no disco local
        return True

    logger.info(f"Arquivo local {file_path} nao encontrado. Tentando baixar do S3...")
    
    s3_client, bucket_name = _get_s3_client()
    if not s3_client:
        return False

    try:
        s3_key = f"Cortex/media/{importacao_lote.arquivo.name}"
        
        # Garante que o diretorio pai local exista
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Faz o download para o local esperado pelo Django
        with open(file_path, 'wb') as f:
            s3_client.download_fileobj(bucket_name, s3_key, f)
            
        logger.info(f"Arquivo baixado do S3 com sucesso para {file_path}")
        return True
    except ClientError as e:
        logger.error(f"Erro de S3 ao baixar o arquivo {s3_key}: {e}")
        return False
    except Exception as e:
        logger.error(f"Erro inesperado ao baixar arquivo do S3 para {file_path}: {e}")
        return False
