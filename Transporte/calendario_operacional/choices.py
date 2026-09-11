from django.db import models


class TipoDiaCalendario(models.TextChoices):
    LETIVO = 'letivo', 'Dia letivo'
    REPOSICAO = 'reposicao', 'Reposição'
    FERIADO = 'feriado', 'Feriado'
    PONTO_FACULTATIVO = 'ponto_facultativo', 'Ponto facultativo'
    SUSPENSAO = 'suspensao', 'Suspensão'
    RECESSO = 'recesso', 'Recesso'
    FERIAS = 'ferias', 'Férias'


TIPOS_OPERACIONAIS = (
    TipoDiaCalendario.LETIVO,
    TipoDiaCalendario.REPOSICAO,
)
