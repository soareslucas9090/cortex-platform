from django.db import models


class StatusExecucaoRota(models.IntegerChoices):
    ABERTA = 1, 'Reservas abertas'
    FECHADA = 2, 'Reservas fechadas'
    EM_EMBARQUE = 3, 'Em embarque'
    FINALIZADA = 4, 'Finalizada'
    CANCELADA = 5, 'Cancelada'
    EMBARCADO = 6, 'Embarcado'
    INICIADA = 7, 'Iniciada'


STATUS_POS_CONFERENCIA = frozenset({
    StatusExecucaoRota.EMBARCADO,
    StatusExecucaoRota.INICIADA,
    StatusExecucaoRota.FINALIZADA,
})

