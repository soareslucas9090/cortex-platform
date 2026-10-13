from datetime import datetime, timedelta

from django.utils import timezone


def calcular_abertura_solicitacoes(data_execucao, horario, horario_saida):
    '''Calcula a abertura no fuso institucional, relativa à data da viagem.'''
    dias_antecedencia = int(horario > horario_saida)
    return timezone.make_aware(
        datetime.combine(data_execucao - timedelta(days=dias_antecedencia), horario),
        timezone.get_current_timezone(),
    )
