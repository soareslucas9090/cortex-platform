from django.db import models

HORAS_ALERTA_ATRASO = 24


class OrigemContaColetiva(models.TextChoices):
    GUARITA = 'guarita', 'Guarita'
    CODIS = 'codis', 'CODIS'


class StatusSolicitacaoTrocaTitular(models.IntegerChoices):
    PENDENTE = 1, 'Pendente'
    ACEITA = 2, 'Aceita'
    RECUSADA = 3, 'Recusada'
    CANCELADA = 4, 'Cancelada'
