from django.db import models


class ResultadoRegistroAcesso(models.IntegerChoices):
    REALIZADO = 1, "Realizado"
    DIVERGENCIA = 2, "Divergência"
    NAO_COMPARECEU = 3, "Não compareceu"
    IMPEDIDO = 4, "Impedido"
