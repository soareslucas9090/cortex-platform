from django.db import models
from django.db.models import Case, IntegerField, Value, When


class DiaSemana(models.TextChoices):
    SEGUNDA = 'segunda', 'Segunda-feira'
    TERCA = 'terca', 'Terça-feira'
    QUARTA = 'quarta', 'Quarta-feira'
    QUINTA = 'quinta', 'Quinta-feira'
    SEXTA = 'sexta', 'Sexta-feira'
    SABADO = 'sabado', 'Sábado'
    DOMINGO = 'domingo', 'Domingo'


def anotacao_ordem_dia_semana(campo='dia_semana'):
    """Anotação para ordenar segunda → domingo em vez da ordem alfabética."""
    whens = [
        When(**{campo: valor}, then=Value(indice))
        for indice, valor in enumerate(DiaSemana.values, start=1)
    ]
    return Case(*whens, default=Value(99), output_field=IntegerField())
