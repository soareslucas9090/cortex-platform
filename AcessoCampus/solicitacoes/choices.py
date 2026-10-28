from datetime import time

from django.db import models


class OrigemSolicitacaoAcesso(models.IntegerChoices):
    ALUNO = 1, 'Aluno'
    GESTAO = 2, 'Gestão'


class TipoSolicitacaoAcesso(models.IntegerChoices):
    ENTRADA = 1, 'Entrada'
    SAIDA = 2, 'Saída'


class StatusSolicitacaoAcesso(models.IntegerChoices):
    PENDENTE = 1, 'Pendente'
    ACEITA = 2, 'Aceito'
    RECUSADA = 3, 'Recusado'


RESULTADO_AVALIACAO = {
    StatusSolicitacaoAcesso.PENDENTE: 'Aguardando análise',
    StatusSolicitacaoAcesso.ACEITA: 'Aprovada',
    StatusSolicitacaoAcesso.RECUSADA: 'Recusada',
}

HORA_AUTORIZADA_PADRAO = time(8, 0)
