from django.db import models


class NivelEnsino(models.IntegerChoices):
    ENSINO_MEDIO = 1, 'Ensino Médio'
    TECNICO = 2, 'Técnico'
    SUPERIOR = 3, 'Superior'
    POS_GRADUACAO = 4, 'Pós-graduação'
