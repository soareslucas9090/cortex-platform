from django.db import models


class StatusTicket(models.IntegerChoices):
    RESERVADO = 1, 'Reservado'
    EM_ESPERA = 2, 'Em espera'
    CANCELADO = 3, 'Cancelado'
    EMBARCADO = 4, 'Embarcado'
    AUSENTE = 5, 'Ausente'

