from django.db import models


class TipoRecurso(models.TextChoices):
    CHAVE = 'chave', 'Chave'
    MIDIA = 'midia', 'Mídia'
    MATERIAL_DIDATICO = 'material_didatico', 'Material didático'


class EstadoRecurso(models.TextChoices):
    AVARIA = 'avaria', 'Em avaria'
    EMPRESTADO = 'emprestado', 'Emprestado'
    RESERVADO = 'reservado', 'Reservado'
    DISPONIVEL = 'disponivel', 'Disponível'
