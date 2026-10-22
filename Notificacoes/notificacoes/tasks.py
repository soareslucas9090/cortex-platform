import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def enviar_envio_task(self, envio_id):
    from .models import Notificacao

    ultima = self.request.retries >= self.max_retries
    try:
        Notificacao().business.processar_envio(
            envio_id,
            ultima_tentativa=ultima,
        )
    except Exception as exc:
        if ultima:
            logger.exception(
                'Falha definitiva ao enviar notificação (envio %s).',
                envio_id,
            )
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
