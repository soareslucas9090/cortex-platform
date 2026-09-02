import os

SPECTACULAR_SETTINGS = {
    'TITLE': os.environ.get('TITLE_API', 'Cortex'),
    'DESCRIPTION': os.environ.get('DESCRIPTION_API', ''),
    'VERSION': os.environ.get('VERSION_API', '1.0.0'),
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [],
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'ENUM_NAME_OVERRIDES': {
        'SituacaoAlunoEnum': 'Academico.alunos.choices.SituacaoAluno',
        'SituacaoMatriculaEnum': 'Identidade.matriculas.choices.SituacaoMatricula',
        'CategoriaServidorEnum': 'PessoasInstitucionais.servidores.choices.CategoriaServidor',
        'CategoriaFuncaoEnum': 'Organizacional.funcoes.choices.CategoriaFuncao',
        'TipoRecursoEnum': 'Infraestrutura.recursos.choices.TipoRecurso',
        'EstadoRecursoEnum': 'Infraestrutura.recursos.choices.EstadoRecurso',
        'DiaSemanaEnum': 'Transporte.rotas.choices.DiaSemana',
        'StatusImportacaoEnum': 'Identidade.usuarios.models.StatusImportacao',
        'StatusExecucaoRotaEnum': 'Transporte.execucoes_rotas.choices.StatusExecucaoRota',
        'StatusTicketEnum': 'Transporte.tickets.choices.StatusTicket',
        'StatusStrikeEnum': 'Transporte.strikes.choices.StatusStrike',
        'StatusJustificativaEnum': 'Transporte.justificativas.choices.StatusJustificativa',
    },
}
