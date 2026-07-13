CAPACIDADES_INFRAESTRUTURA = (
    'operar',
    'cadastrar',
    'autorizar',
    'retirada_irrestrita',
)


def capacidades_infraestrutura_vazias() -> dict:
    """Retorna todas as capacidades do módulo desligadas."""
    return {capacidade: False for capacidade in CAPACIDADES_INFRAESTRUTURA}
