'''Constantes do app de solicitações de acesso.'''
from datetime import time

from AppCore.common.storage.anexo import AnexoS3

from AcessoCampus.tipos.choices import NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS

'''
Comprovante obrigatório anexado pelo aluno ao pedir acesso.
A chave segue ``{prefixo}/{aluno_id}/{uuid}.{ext}`` (upload antes da criação da solicitação).
O GET do proxy é autenticado e restrito ao aluno dono e à gestão com escopo sobre ele:
o comprovante pode conter dado sensível (ex.: saúde) e não segue o modelo público da foto.
'''
ANEXO_COMPROVANTE = AnexoS3(
    prefixo='Cortex/acesso-campus/solicitacoes/comprovantes',
    nome_url='acesso_campus:solicitacao-anexo',
    caminho_fallback='/cortex/acesso-campus/solicitacoes/{id}/anexo/',
)

'''Extensão gravada no S3 por content-type aceito para o comprovante.'''
EXTENSOES_ANEXO_POR_CONTENT_TYPE = {
    'application/pdf': 'pdf',
    'image/jpeg': 'jpg',
    'image/png': 'png',
}

'''
Assinaturas (bytes iniciais) usadas para identificar o tipo real do comprovante,
independentemente do content-type informado pelo cliente.
'''
ASSINATURAS_ANEXO = (
    (b'%PDF-', 'application/pdf'),
    (b'\x89PNG\r\n\x1a\n', 'image/png'),
    (b'\xff\xd8\xff', 'image/jpeg'),
)

'''Tamanho máximo do comprovante (5 MB), igual ao limite validado no MeuIF.'''
TAMANHO_MAXIMO_ANEXO_BYTES = 5 * 1024 * 1024

'''Limites de texto do formulário do aluno no MeuIF.'''
TAMANHO_MAXIMO_MOTIVO_ALUNO = 100
TAMANHO_MAXIMO_JUSTIFICATIVA_ALUNO = 500

'''
Tipos do catálogo que o aluno pode pedir: só os dois tipos-base.
Os tipos criados pela gestão servem apenas às autorizações registradas por ela.
'''
NOMES_TIPOS_DO_ALUNO = (NOME_TIPO_ENTRADA_CAMPUS, NOME_TIPO_SAIDA_CAMPUS)

'''
Prazo do pedido de entrada para o próprio dia: até 07:00 (America/Fortaleza).
Datas futuras podem ser pedidas a qualquer horário; saída não tem prazo.
'''
LIMITE_SOLICITACAO_ENTRADA_MESMO_DIA = time(7, 0)

'''
Valores aceitos em ``ordenacao`` na listagem do aluno (colunas ordenáveis do MeuIF);
o prefixo ``-`` inverte a direção. Valor fora da lista usa ORDENACAO_PADRAO_ALUNO.
'''
ORDENACOES_ALUNO = (
    'data_liberacao',
    '-data_liberacao',
    'data_solicitacao',
    '-data_solicitacao',
    'tipo',
    '-tipo',
    'motivo',
    '-motivo',
    'avaliado_por',
    '-avaliado_por',
)

'''Ordem padrão da listagem do aluno: pedidos mais recentes primeiro.'''
ORDENACAO_PADRAO_ALUNO = '-data_solicitacao'
