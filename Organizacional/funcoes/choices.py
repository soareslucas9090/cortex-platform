from django.db import models


class CategoriaFuncao(models.TextChoices):
    DIRETOR = 'diretor', 'Diretor'
    COORDENADOR = 'coordenador', 'Coordenador'
    CHEFE = 'chefe', 'Chefe'
