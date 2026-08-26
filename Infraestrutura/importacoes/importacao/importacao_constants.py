ABA_BLOCO = 'bloco'
ABA_SALA = 'sala'
ABA_RECURSO = 'recurso'

ABAS_OPERACIONAIS = [
    ABA_BLOCO,
    ABA_SALA,
    ABA_RECURSO,
]

ABAS_OBRIGATORIAS_MINIMAS = [
    ABA_BLOCO,
]

COLUNAS_ABA_BLOCO = [
    'bloco_id',
    'nome',
]

COLUNAS_ABA_SALA = [
    'sala_id',
    'bloco_id',
    'nome',
]

COLUNAS_ABA_RECURSO = [
    'sala_id',
    'descricao',
    'codigo',
    'avaria',
    'tipo',
    'foto',
]

ALIAS_CABECALHOS_IMPORTACAO = {}

COLUNAS_ESPERADAS_POR_ABA = {
    ABA_BLOCO: COLUNAS_ABA_BLOCO,
    ABA_SALA: COLUNAS_ABA_SALA,
    ABA_RECURSO: COLUNAS_ABA_RECURSO,
}

DEPENDENCIAS_ENTRE_ABAS = {
    ABA_SALA: [ABA_BLOCO],
    ABA_RECURSO: [ABA_SALA],
}

CODIGO_ERRO_ARQUIVO_INVALIDO = 'arquivo_invalido'
CODIGO_ERRO_EXTENSAO_INVALIDA = 'extensao_invalida'
CODIGO_ERRO_ABA_OBRIGATORIA_AUSENTE = 'aba_obrigatoria_ausente'
CODIGO_ERRO_COLUNAS_OBRIGATORIAS_AUSENTES = 'colunas_obrigatorias_ausentes'
CODIGO_ERRO_LINHA_INVALIDA = 'linha_invalida'
CODIGO_ERRO_FOTO = 'erro_foto'

EXTENSOES_SUPORTADAS = ['.ods']

TIPOS_RECURSO_VALIDOS = ['chave', 'midia', 'material_didatico']
