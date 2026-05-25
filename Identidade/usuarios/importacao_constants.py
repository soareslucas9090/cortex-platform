ABA_USUARIO = 'Usuario'
ABA_CONTATO = 'Contato'
ABA_ENDERECO = 'Endereco'
ABA_MATRICULA = 'Matricula'
ABA_ALUNO = 'Aluno'
ABA_CURSO = 'Curso'
ABA_ALUNO_CURSO = 'Aluno_Curso'
ABA_SERVIDOR = 'Servidor'
ABA_CARGO = 'Cargo'
ABA_TERCEIRIZADO = 'Terceirizado'
ABA_EMPRESA_INSTITUICAO = 'Empresa_Instituicao'
ABA_SETOR = 'Setor'
ABA_FUNCAO = 'Funcao'
ABA_SETOR_LOTACAO = 'Setor_Lotacao'

ABAS_OPERACIONAIS = [
    ABA_USUARIO,
    ABA_CONTATO,
    ABA_ENDERECO,
    ABA_MATRICULA,
    ABA_ALUNO,
    ABA_ALUNO_CURSO,
    ABA_SERVIDOR,
    ABA_TERCEIRIZADO,
    ABA_SETOR_LOTACAO,
]

ABAS_REFERENCIA = [
    ABA_CURSO,
    ABA_CARGO,
    ABA_EMPRESA_INSTITUICAO,
    ABA_SETOR,
    ABA_FUNCAO,
]

ABAS_OBRIGATORIAS_MINIMAS = [
    ABA_USUARIO,
]

COLUNAS_ABA_USUARIO = [
    'usuario_id',
    'cpf',
    'nome',
    'foto',
    'deficiencia',
    'ativo',
    'ultimo_login',
]

COLUNAS_ABA_CONTATO = [
    'usuario_id',
    'email_academico',
    'email_pessoal',
    'telefone',
]

COLUNAS_ABA_ENDERECO = [
    'usuario_id',
    'endereco',
    'bairro',
    'cep',
    'complemento',
    'numero',
    'cidade',
    'estado',
]

COLUNAS_ABA_MATRICULA = [
    'usuario_id',
    'matricula',
    'situacao',
]

COLUNAS_ABA_ALUNO = [
    'aluno_id',
    'usuario_id',
    'ira',
]

COLUNAS_ABA_ALUNO_CURSO = [
    'aluno_id',
    'curso_id',
    'ano_conclusao',
]

COLUNAS_ABA_SERVIDOR = [
    'servidor_id',
    'usuario_id',
    'cargo_id',
    'categoria',
    'ativo',
]

COLUNAS_ABA_TERCEIRIZADO = [
    'terceirizado_id',
    'usuario_id',
    'empresa_instituicao_id',
    'ativo',
]

COLUNAS_ABA_SETOR_LOTACAO = [
    'usuario_id',
    'setor_id',
    'funcao_id',
    'responsavel',
    'monitor',
]

COLUNAS_ESPERADAS_POR_ABA = {
    ABA_USUARIO: COLUNAS_ABA_USUARIO,
    ABA_CONTATO: COLUNAS_ABA_CONTATO,
    ABA_ENDERECO: COLUNAS_ABA_ENDERECO,
    ABA_MATRICULA: COLUNAS_ABA_MATRICULA,
    ABA_ALUNO: COLUNAS_ABA_ALUNO,
    ABA_ALUNO_CURSO: COLUNAS_ABA_ALUNO_CURSO,
    ABA_SERVIDOR: COLUNAS_ABA_SERVIDOR,
    ABA_TERCEIRIZADO: COLUNAS_ABA_TERCEIRIZADO,
    ABA_SETOR_LOTACAO: COLUNAS_ABA_SETOR_LOTACAO,
}

DEPENDENCIAS_ENTRE_ABAS = {
    ABA_CONTATO: [ABA_USUARIO],
    ABA_ENDERECO: [ABA_USUARIO],
    ABA_MATRICULA: [ABA_USUARIO],
    ABA_ALUNO: [ABA_USUARIO],
    ABA_ALUNO_CURSO: [ABA_ALUNO],
    ABA_SERVIDOR: [ABA_USUARIO],
    ABA_TERCEIRIZADO: [ABA_USUARIO],
    ABA_SETOR_LOTACAO: [ABA_USUARIO],
}

CODIGO_ERRO_ARQUIVO_INVALIDO = 'arquivo_invalido'
CODIGO_ERRO_EXTENSAO_INVALIDA = 'extensao_invalida'
CODIGO_ERRO_ABA_OBRIGATORIA_AUSENTE = 'aba_obrigatoria_ausente'
CODIGO_ERRO_COLUNAS_OBRIGATORIAS_AUSENTES = 'colunas_obrigatorias_ausentes'
CODIGO_ERRO_LINHA_INVALIDA = 'linha_invalida'
CODIGO_ERRO_REFERENCIA_NAO_ENCONTRADA = 'referencia_nao_encontrada'
CODIGO_ERRO_CARDINALIDADE_INVALIDA = 'cardinalidade_invalida'
CODIGO_ERRO_MAPEAMENTO_INTERNO_INVALIDO = 'mapeamento_interno_invalido'
CODIGO_ERRO_CPF_INVALIDO = 'cpf_invalido'
CODIGO_ERRO_DATA_INVALIDA = 'data_invalida'
CODIGO_ERRO_BOOLEANO_INVALIDO = 'booleano_invalido'
CODIGO_ERRO_INTEIRO_INVALIDO = 'inteiro_invalido'
CODIGO_ERRO_DECIMAL_INVALIDO = 'decimal_invalido'
CODIGO_ERRO_EMAIL_INVALIDO = 'email_invalido'

EXTENSOES_SUPORTADAS = ['.ods']