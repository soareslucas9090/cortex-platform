from django.db import models


class StatusStrike(models.IntegerChoices):
    ATIVO = 1, 'Ativo'
    JUSTIFICADO = 2, 'Justificado'

