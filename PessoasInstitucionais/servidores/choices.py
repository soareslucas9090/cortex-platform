from django.db import models


class CategoriaServidor(models.IntegerChoices):
    DOCENTE = 1, 'Professor'
    TECNICO_ADMINISTRATIVO = 2, 'Tec.Administrativo'
