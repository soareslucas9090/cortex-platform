from datetime import time


HORARIO_ABERTURA_SOLICITACOES = time(19, 0)

FASE_CONFERENCIA_PRIMEIRA = 'primeira'
FASE_CONFERENCIA_SEGUNDA = 'segunda'
FASE_CONFERENCIA_CPF = 'cpf'
FASE_CONFERENCIA_ENCERRADA = 'encerrada'

MENSAGEM_SEGUNDA_CHAMADA_PULADA = (
    'A segunda chamada foi dispensada porque não havia tickets reservados pendentes.'
)
MENSAGEM_RESERVADOS_PENDENTES = (
    'Ainda há tickets reservados. Marque presença, ausência ou use Restantes faltaram '
    'antes de encerrar esta etapa.'
)
MENSAGEM_FASE_CPF_INDISPONIVEL = (
    'A entrada por CPF só é permitida após encerrar a chamada de tickets.'
)
MENSAGEM_CONFERENCIA_JA_ENCERRADA = 'A conferência desta execução já foi finalizada.'
