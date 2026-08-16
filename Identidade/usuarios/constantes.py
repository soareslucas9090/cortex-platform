'''Constantes do app de usuários.'''
from AppCore.common.storage.anexo import AnexoS3

'''
Anexo S3 da foto secundária do usuário (prefixo no bucket, nome da rota de proxy
e path de fallback). Usado no upload/remoção (business), na URL pública
(serializer) e no stream do GET. Centraliza prefixo e rota para não espalhar
esses valores pelas camadas nem criar um arquivo só para a foto.
'''
ANEXO_FOTO_SECUNDARIA = AnexoS3(
    prefixo='Cortex/usuarios/fotos',
    nome_url='identidade:usuario-foto-secundaria',
    caminho_fallback='/cortex/identidade/usuarios/{id}/foto-secundaria/',
)
