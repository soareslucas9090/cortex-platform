from django.db import models


class SituacaoMatricula(models.IntegerChoices):
    ATIVA = 1, 'Ativa'
    INATIVA = 2, 'Inativa'
