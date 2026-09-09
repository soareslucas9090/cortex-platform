import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def gerar_execucoes_rotas_automaticas_task():
    from .models import ExecucaoRota

    resultado = ExecucaoRota().business.gerar_execucoes_automaticas()
    logger.info(
        'Geração automática de execuções concluída para %(data_execucao)s: '
        '%(criadas)s criada(s), %(existentes)s existente(s) e '
        '%(fora_do_prazo)s fora do prazo. Dia operacional: %(dia_operacional)s.',
        resultado,
    )
    if resultado['conflitos_execucoes_existentes']:
        logger.warning(
            'A data %(data_execucao)s não é operacional, mas possui execuções '
            'ativas cadastradas: %(conflitos_execucoes_existentes)s.',
            resultado,
        )
    return resultado
