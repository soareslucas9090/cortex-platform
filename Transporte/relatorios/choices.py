from django.db import models


class CategoriaRelatorioAluno(models.TextChoices):
    PRESENTES = 'presentes', 'Presentes'
    AUSENCIAS = 'ausencias', 'Ausências'
    BLOQUEIOS = 'bloqueios', 'Bloqueios'
    SEM_TICKET = 'sem_ticket', 'Sem ticket'
