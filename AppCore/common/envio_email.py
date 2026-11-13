from django.conf import settings

from AppCore.common.tasks import send_simple_email_task
from AppCore.core.exceptions.exceptions import SystemErrorException, ValidationException


def enviar_email(destinatarios, assunto, html, texto='', remetente=None):
    """Enfileira um e-mail HTML. O envio ocorre no worker Celery, nunca na request."""
    if isinstance(destinatarios, str):
        destinatarios = [destinatarios]
    destinatarios = [item.strip() for item in (destinatarios or []) if item and str(item).strip()]
    if not destinatarios:
        raise ValidationException('Informe ao menos um destinatário.')

    if remetente is None:
        remetente = settings.FROM_EMAIL_NOREPLY
    remetente = (remetente or '').strip()
    if not remetente:
        raise ValidationException('Remetente de e-mail não configurado.')

    try:
        send_simple_email_task.delay(assunto, texto, remetente, destinatarios, html)
    except Exception as err:
        raise SystemErrorException('Não foi possível enfileirar o e-mail.') from err
