from django.db import models


class StatusEventoAcesso(models.TextChoices):
    PENDENTE = 'PENDENTE', 'Pendente'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'
    EXPIRADA = 'EXPIRADA', 'Expirada'


class TipoBeneficiarioAcesso(models.TextChoices):
    INDIVIDUAL = 'INDIVIDUAL', 'Individual'
    TURMA = 'TURMA', 'Turma'
