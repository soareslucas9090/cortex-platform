from django.db import models


class DiaSemana(models.TextChoices):
    SEGUNDA = 'segunda', 'Segunda-feira'
    TERCA = 'terca', 'Terça-feira'
    QUARTA = 'quarta', 'Quarta-feira'
    QUINTA = 'quinta', 'Quinta-feira'
    SEXTA = 'sexta', 'Sexta-feira'
    SABADO = 'sabado', 'Sábado'
    DOMINGO = 'domingo', 'Domingo'
