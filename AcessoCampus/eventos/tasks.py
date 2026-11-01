from celery import shared_task
from django.db import transaction

from .models import EventoAcesso


@shared_task
def expirar_eventos_acesso_task():
    with transaction.atomic():
        return EventoAcesso().business.expirar_pendentes()
