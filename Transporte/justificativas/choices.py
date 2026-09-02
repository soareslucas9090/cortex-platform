from django.db import models


class StatusJustificativa(models.IntegerChoices):
    PENDENTE = 1, 'Pendente'
    APROVADA = 2, 'Aprovada'
    REJEITADA = 3, 'Rejeitada'

