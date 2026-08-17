'''Constantes do app de recursos.'''
from AppCore.common.storage.anexo import AnexoS3

'''
Anexo S3 da foto do recurso (prefixo no bucket, nome da rota de proxy e path de
fallback). Usado no upload/remoção (business), na URL pública (serializer) e no
stream do GET. Centraliza prefixo e rota para o próximo anexo não ganhar um
arquivo próprio.
'''
ANEXO_FOTO = AnexoS3(
    prefixo='Cortex/infraestrutura/recursos/fotos',
    nome_url='infraestrutura:recurso-foto',
    caminho_fallback='/cortex/infraestrutura/recursos/{id}/foto/',
)

'''Proporção de largura do recorte central obrigatório da foto do recurso (3:4).'''
PROPORCAO_FOTO_LARGURA = 3

'''Proporção de altura do recorte central obrigatório da foto do recurso (3:4).'''
PROPORCAO_FOTO_ALTURA = 4

'''Largura mínima em pixels após o recorte 3:4; usada na validação em rules.'''
LARGURA_MINIMA_FOTO = 480

'''Altura mínima em pixels após o recorte 3:4; usada na validação em rules.'''
ALTURA_MINIMA_FOTO = 640
