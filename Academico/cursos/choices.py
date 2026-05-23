from django.db import models


class TurnoCurso(models.IntegerChoices):
    MATUTINO = 1, 'Matutino'
    VESPERTINO = 2, 'Vespertino'
    NOTURNO = 3, 'Noturno'
    INTEGRAL = 4, 'Integral'
