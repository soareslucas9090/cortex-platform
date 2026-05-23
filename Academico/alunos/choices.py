from django.db import models


class SituacaoAluno(models.IntegerChoices):
    MATRICULADO = 1, 'Matriculado'
    TRANCADO = 2, 'Trancado'
    FORMADO = 3, 'Formado'
    DESISTENTE = 4, 'Desistente'
    TRANSFERIDO = 5, 'Transferido'


class FormaIngresso(models.IntegerChoices):
    VESTIBULAR = 1, 'Vestibular'
    ENEM = 2, 'ENEM'
    TRANSFERENCIA = 3, 'Transferência'
    REINGRESSO = 4, 'Reingresso'
