'''Configuração de armazenamento da foto secundária do usuário.'''

PREFIXO_S3 = 'Cortex/usuarios/fotos'
NOME_URL_PROXY = 'identidade:usuario-foto-secundaria'


def caminho_fallback_proxy(usuario_id: int) -> str:
    return f'/cortex/identidade/usuarios/{usuario_id}/foto-secundaria/'
