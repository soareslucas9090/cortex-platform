CAPACIDADES_TRANSPORTE_FUNCAO = ('conferir', 'visualizar_relatorio_alunos')


def capacidades_transporte_vazias() -> dict:
    return {
        'gerenciar': False,
        'motorista': False,
        'reservar': False,
        'conferir': False,
        'visualizar_relatorio_alunos': False,
        'bloqueado': False,
        'faltas': 0,
        'bloqueios': 0,
    }
