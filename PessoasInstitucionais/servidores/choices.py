from django.db import models


class CategoriaServidor(models.IntegerChoices):
    DOCENTE = 1, 'Docente'
    TECNICO_ADMINISTRATIVO = 2, 'Técnico-Administrativo'
