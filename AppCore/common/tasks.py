from celery import shared_task
from celery.utils.log import get_task_logger

from AppCore.common.util.util import enviar_email_simples

logger = get_task_logger(__name__)


@shared_task(
    name='AppCore.common.tasks.send_simple_email_task',
    bind=True,
    max_retries=4,
    default_retry_delay=30,
)
def send_simple_email_task(self, subject, simple_text, from_email, to_emails, html_content):
    try:
        enviar_email_simples(subject, simple_text, from_email, to_emails, html_content)
    except Exception as exc:
        logger.exception(
            'Falha ao enviar email (tentativa %s/%s): %s',
            self.request.retries + 1,
            self.max_retries + 1,
            exc,
        )
        raise self.retry(exc=exc, countdown=30)
