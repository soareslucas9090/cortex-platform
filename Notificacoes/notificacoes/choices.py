from django.db import models

CanalSistema = 'sistema'

CANAIS_DISPONIVEIS = frozenset(
    {
        CanalSistema,
        'email',
        'sms',
        'whatsapp',
    }
)


class CanalEnvio(models.TextChoices):
    EMAIL = 'email', 'E-mail'
    SMS = 'sms', 'SMS'
    WHATSAPP = 'whatsapp', 'WhatsApp'


class StatusEnvio(models.TextChoices):
    PENDENTE = 'pendente', 'Pendente'
    ENVIADO = 'enviado', 'Enviado'
    FALHOU = 'falhou', 'Falhou'
    IGNORADO = 'ignorado', 'Ignorado'
