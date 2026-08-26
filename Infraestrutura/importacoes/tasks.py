from celery import shared_task
import logging

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_FATAL_IMPORTACAO = 'Falha interna na importação.'


def _importacao_ainda_em_andamento(importacao):
    from .models import StatusImportacao

    importacao.refresh_from_db()
    return importacao.status == StatusImportacao.EM_ANDAMENTO


@shared_task
def processar_importacao_infraestrutura_task(importacao_id):
    from .models import ImportacaoLote, StatusImportacao

    try:
        importacao = ImportacaoLote.objects.get(id=importacao_id)
    except ImportacaoLote.DoesNotExist:
        logger.error('Importação %s não encontrada.', importacao_id)
        return

    if importacao.status != StatusImportacao.EM_ANDAMENTO:
        logger.info(
            'Importação %s não está em andamento (status=%s). Abortando.',
            importacao_id,
            importacao.status,
        )
        return

    try:
        from .importacao.s3_helper import download_importacao_from_s3_if_needed

        if not download_importacao_from_s3_if_needed(importacao):
            if not _importacao_ainda_em_andamento(importacao):
                return
            importacao.status = StatusImportacao.ERRO
            resultado = importacao.resultado_json or {}
            if not isinstance(resultado, dict):
                resultado = {}
            resultado['erro_fatal'] = MENSAGEM_ERRO_FATAL_IMPORTACAO
            importacao.resultado_json = resultado
            importacao.save()
            return

        resultado = importacao.business.importar_infraestrutura_em_lote(importacao)

        if not _importacao_ainda_em_andamento(importacao):
            logger.info(
                'Importação %s foi interrompida (status=%s). Não sobrescrever.',
                importacao_id,
                importacao.status,
            )
            return

        importacao.status = StatusImportacao.CONCLUIDA
        importacao.resultado_json = {
            'resumo': resultado.resumo.__dict__,
            'erros': [erro.__dict__ for erro in resultado.erros],
        }
        importacao.save()

    except Exception as exc:
        logger.exception(
            'Erro catastrófico na importação %s: %s', importacao_id, exc
        )
        try:
            if not _importacao_ainda_em_andamento(importacao):
                return
            importacao.status = StatusImportacao.ERRO
            resultado = importacao.resultado_json or {}
            if not isinstance(resultado, dict):
                resultado = {}
            if 'erro_fatal' not in resultado:
                resultado['erro_fatal'] = MENSAGEM_ERRO_FATAL_IMPORTACAO
            importacao.resultado_json = resultado
            importacao.save()
        except Exception as save_exc:
            logger.exception(
                'Erro ao salvar status de erro da importação %s: %s',
                importacao_id,
                save_exc,
            )
