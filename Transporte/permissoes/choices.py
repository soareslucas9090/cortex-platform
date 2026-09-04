CAPACIDADES_TRANSPORTE_FUNCAO = ('conferir',)


def capacidades_transporte_vazias() -> dict:
    return {'gerenciar': False, 'motorista': False, 'reservar': False, 'conferir': False, 'bloqueado': False, 'faltas': 0, 'bloqueios': 0}
