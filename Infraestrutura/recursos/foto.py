'''Configuração de armazenamento e recorte da foto do recurso.'''

PREFIXO_S3 = 'Cortex/infraestrutura/recursos/fotos'
NOME_URL_PROXY = 'infraestrutura:recurso-foto'
PROPORCAO_LARGURA = 3
PROPORCAO_ALTURA = 4
LARGURA_MINIMA = 480
ALTURA_MINIMA = 640


def caminho_fallback_proxy(recurso_id: int) -> str:
    return f'/cortex/infraestrutura/recursos/{recurso_id}/foto/'
