CAPACIDADES_ACESSO_CAMPUS = (
    'solicitar',
    'analisar_solicitacoes',
    'operar_portaria',
    'visualizar_historico',
)


def capacidades_acesso_campus_vazias() -> dict:
    return {capacidade: False for capacidade in CAPACIDADES_ACESSO_CAMPUS}


def capacidades_acesso_campus_completas() -> dict:
    return {capacidade: True for capacidade in CAPACIDADES_ACESSO_CAMPUS}
