ABA_USUARIO = 'Usuario'
ABA_CONTATO = 'Contato'
ABA_ENDERECO = 'Endereco'
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
    ABA_ALUNO,
    ABA_CURSO,
    ABA_ALUNO_CURSO,
    ABA_SERVIDOR,
    ABA_TERCEIRIZADO,
    ABA_SETOR_LOTACAO,
]

ABAS_REFERENCIA = [
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
    'ativo',
    'ultimo_login',
    'colaborador_externo',
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
    'cidade',
    'estado',
]

COLUNAS_ABA_ALUNO = [
    'aluno_id',
    'usuario_id',
    'ira',
    'deficiencia',
]

COLUNAS_ABA_ALUNO_CURSO = [
    'aluno_id',
    'curso_id',
    'ano_conclusao',
    'matricula',
    'ira',
    'turma',
    'turno',
    'situacao_curso',
]

COLUNAS_ABA_SERVIDOR = [
    'servidor_id',
    'usuario_id',
    'cargo_id',
    'categoria',
    'ativo',
    'matricula',
]

COLUNAS_ABA_TERCEIRIZADO = [
    'terceirizado_id',
    'usuario_id',
    'empresa_instituicao_id',
    'ativo',
    'matricula',
]

COLUNAS_ABA_SETOR_LOTACAO = [
    'usuario_id',
    'setor_id',
    'funcao_id',
    'responsavel',
    'monitor',
]

COLUNAS_ABA_SETOR_REFERENCIA = [
    'setor_id',
    'nome',
    'sigla',
    'ativo',
]

COLUNAS_ABA_FUNCAO_REFERENCIA = [
    'funcao_id',
    'papel_funcao',
    'descricao',
    'ativo',
]

# Aliases de cabeçalho da planilha → nome canônico interno
ALIAS_CABECALHOS_IMPORTACAO = {
    'funcao': 'papel_funcao',
}

COLUNAS_ABA_CARGO_REFERENCIA = [
    'cargo_id',
    'nome',
    'ativo',
]

COLUNAS_ABA_CURSO_REFERENCIA = [
    'curso_id',
    'setor_id',
    'nome',
    'codigo_curso',
    'ativo',
]

COLUNAS_ABA_EMPRESA_INSTITUICAO_REFERENCIA = [
    'empresa_instituicao_id',
    'nome',
    'ativo',
]

COLUNAS_ESPERADAS_POR_ABA = {
    ABA_USUARIO: COLUNAS_ABA_USUARIO,
    ABA_CONTATO: COLUNAS_ABA_CONTATO,
    ABA_ENDERECO: COLUNAS_ABA_ENDERECO,
    ABA_ALUNO: COLUNAS_ABA_ALUNO,
    ABA_ALUNO_CURSO: COLUNAS_ABA_ALUNO_CURSO,
    ABA_SERVIDOR: COLUNAS_ABA_SERVIDOR,
    ABA_TERCEIRIZADO: COLUNAS_ABA_TERCEIRIZADO,
    ABA_SETOR_LOTACAO: COLUNAS_ABA_SETOR_LOTACAO,
    ABA_SETOR: COLUNAS_ABA_SETOR_REFERENCIA,
    ABA_FUNCAO: COLUNAS_ABA_FUNCAO_REFERENCIA,
    ABA_CARGO: COLUNAS_ABA_CARGO_REFERENCIA,
    ABA_CURSO: COLUNAS_ABA_CURSO_REFERENCIA,
    ABA_EMPRESA_INSTITUICAO: COLUNAS_ABA_EMPRESA_INSTITUICAO_REFERENCIA,
}

DEPENDENCIAS_ENTRE_ABAS = {
    ABA_CONTATO: [ABA_USUARIO],
    ABA_ENDERECO: [ABA_USUARIO],
    ABA_ALUNO: [ABA_USUARIO],
    ABA_CURSO: [ABA_SETOR],
    ABA_ALUNO_CURSO: [ABA_ALUNO, ABA_CURSO],
    ABA_SERVIDOR: [ABA_USUARIO, ABA_CARGO],
    ABA_TERCEIRIZADO: [ABA_USUARIO, ABA_EMPRESA_INSTITUICAO],
    ABA_SETOR_LOTACAO: [ABA_USUARIO, ABA_SETOR, ABA_FUNCAO],
}

ATTR_ID_PLANILHA_POR_ABA = {
    ABA_USUARIO: 'usuario_id_planilha',
    ABA_ALUNO: 'aluno_id_planilha',
    ABA_CURSO: 'curso_id_planilha',
    ABA_SERVIDOR: 'servidor_id_planilha',
    ABA_TERCEIRIZADO: 'terceirizado_id_planilha',
    ABA_SETOR: 'setor_id_planilha',
    ABA_FUNCAO: 'funcao_id_planilha',
    ABA_CARGO: 'cargo_id_planilha',
    ABA_EMPRESA_INSTITUICAO: 'empresa_instituicao_id_planilha',
}

COLECAO_POR_ABA = {
    ABA_SETOR: 'setores',
    ABA_FUNCAO: 'funcoes',
    ABA_CARGO: 'cargos',
    ABA_EMPRESA_INSTITUICAO: 'empresas',
    ABA_USUARIO: 'usuarios',
    ABA_CONTATO: 'contatos',
    ABA_ENDERECO: 'enderecos',
    ABA_ALUNO: 'alunos',
    ABA_CURSO: 'cursos',
    ABA_ALUNO_CURSO: 'alunos_cursos',
    ABA_SERVIDOR: 'servidores',
    ABA_TERCEIRIZADO: 'terceirizados',
    ABA_SETOR_LOTACAO: 'setores_lotacao',
}

DEPENDENCIAS_DE_LINHA = {
    ABA_CONTATO: [
        {'campo': 'usuario_id', 'aba_pai': ABA_USUARIO, 'attr': 'usuario_id_planilha'},
    ],
    ABA_ENDERECO: [
        {'campo': 'usuario_id', 'aba_pai': ABA_USUARIO, 'attr': 'usuario_id_planilha'},
    ],
    ABA_ALUNO: [
        {'campo': 'usuario_id', 'aba_pai': ABA_USUARIO, 'attr': 'usuario_id_planilha'},
    ],
    ABA_SERVIDOR: [
        {'campo': 'usuario_id', 'aba_pai': ABA_USUARIO, 'attr': 'usuario_id_planilha'},
        {'campo': 'cargo_id', 'aba_pai': ABA_CARGO, 'attr': 'cargo_id_planilha'},
    ],
    ABA_TERCEIRIZADO: [
        {'campo': 'usuario_id', 'aba_pai': ABA_USUARIO, 'attr': 'usuario_id_planilha'},
        {
            'campo': 'empresa_instituicao_id',
            'aba_pai': ABA_EMPRESA_INSTITUICAO,
            'attr': 'empresa_instituicao_id_planilha',
        },
    ],
    ABA_SETOR_LOTACAO: [
        {'campo': 'usuario_id', 'aba_pai': ABA_USUARIO, 'attr': 'usuario_id_planilha'},
        {'campo': 'setor_id', 'aba_pai': ABA_SETOR, 'attr': 'setor_id_planilha'},
        {
            'campo': 'funcao_id',
            'aba_pai': ABA_FUNCAO,
            'attr': 'funcao_id_planilha',
            'opcional': True,
        },
    ],
    ABA_CURSO: [
        {'campo': 'setor_id', 'aba_pai': ABA_SETOR, 'attr': 'setor_id_planilha'},
    ],
    ABA_ALUNO_CURSO: [
        {'campo': 'aluno_id', 'aba_pai': ABA_ALUNO, 'attr': 'aluno_id_planilha'},
        {'campo': 'curso_id', 'aba_pai': ABA_CURSO, 'attr': 'curso_id_planilha'},
    ],
}

PAPEL_ERRO_CAUSA = 'causa'
PAPEL_ERRO_IMPACTO = 'impacto'

TIPO_GRUPO_FALHA_ENTIDADE = 'falha_entidade'
TIPO_GRUPO_REFERENCIA_INEXISTENTE = 'referencia_inexistente'
TIPO_GRUPO_LINHA = 'linha'

MAX_GRUPOS_ERRO_API = 50
MAX_ERROS_PLANOS_API = 50
MAX_IMPACTOS_POR_GRUPO_API = 20

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