import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def enviar_envio_task(self, envio_id):
    from .choices import StatusEnvio
    from .models import Envio, Notificacao

    try:
        envio = Envio.objects.get(pk=envio_id)
    except Envio.DoesNotExist:
        logger.warning('Envio %s não encontrado para envio assíncrono.', envio_id)
        return

    if envio.status in (StatusEnvio.ENVIADO, StatusEnvio.IGNORADO):
        return

    try:
        Notificacao().business.processar_envio(envio_id)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            envio.status = StatusEnvio.FALHOU
            envio.ultimo_erro = 'Falha ao enviar notificação.'
            envio.save(update_fields=['status', 'ultimo_erro', 'updated_at'])
            logger.exception(
                'Falha definitiva ao enviar notificação (envio %s).',
                envio_id,
            )
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
