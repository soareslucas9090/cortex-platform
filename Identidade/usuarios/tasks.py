from celery import shared_task
from django.db import transaction
import logging
from AppCore.core.exceptions.exceptions import ValidationException

logger = logging.getLogger(__name__)

@shared_task
def processar_importacao_usuarios_task(importacao_id):
    from .models import ImportacaoLote, StatusImportacao
    from .business import UsuarioBusiness

    try:
        importacao = ImportacaoLote.objects.get(id=importacao_id)
    except ImportacaoLote.DoesNotExist:
        logger.error(f"Importação {importacao_id} não encontrada.")
        return

    try:
        # Passa a importacao para o business para atualizar o progresso
        resultado = UsuarioBusiness().importar_usuarios_em_lote(importacao)
        
        # Após concluir, atualiza o status baseado no resultado
        if resultado.sucesso:
            importacao.status = StatusImportacao.CONCLUIDA
        else:
            # Pode ser considerado concluída com parcial sucesso ou Erro dependendo do domínio
            # Se for sucesso parcial (erros != 0 mas success = True), vou manter CONCLUIDA, mas com erros.
            importacao.status = StatusImportacao.CONCLUIDA
            
        importacao.resultado_json = {
            'resumo': resultado.resumo.__dict__,
            'erros': [erro.__dict__ for erro in resultado.erros],
        }
        importacao.save()
        
    except Exception as exc:
        logger.exception(f"Erro catastrófico na importação {importacao_id}: {exc}")
        try:
            importacao.refresh_from_db()
            importacao.status = StatusImportacao.ERRO
            resultado = importacao.resultado_json or {}
            if not isinstance(resultado, dict):
                resultado = {}
            if 'erro_fatal' not in resultado:
                resultado['erro_fatal'] = str(exc)
            importacao.resultado_json = resultado
            importacao.save()
        except Exception as save_exc:
            logger.exception(f"Erro ao salvar status de erro da importação {importacao_id}: {save_exc}")
