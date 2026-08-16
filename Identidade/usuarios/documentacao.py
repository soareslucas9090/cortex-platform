from .choices import (
    NIVEL_CORTEX,
    PERMISSAO_CORTEX_EDITAR_EU,
    PERMISSAO_CORTEX_EDITAR_TUDO,
    PERMISSAO_CORTEX_LER_TUDO,
)


class PermissaoDocumentacao:
    """Registro de documentação narrativa das permissões por módulo."""

    @classmethod
    def compilar_documentacao(cls) -> list:
        modulos = []
        for attr_name in dir(cls):
            if attr_name.startswith('documentacao_') and attr_name != 'documentacao_':
                metodo = getattr(cls, attr_name)
                if callable(metodo):
                    resultado = metodo()
                    if isinstance(resultado, dict):
                        modulos.append(resultado)
        return sorted(modulos, key=lambda m: m.get('chave', ''))

    @classmethod
    def documentacao_cortex(cls) -> dict:
        return {
            'chave': 'cortex',
            'titulo': 'Cortex (plataforma)',
            'resumo': (
                'Três níveis hierárquicos de acesso derivados da identidade do usuário. '
                'Outros produtos (ex.: Infraestrutura) podem definir níveis ou capacidades próprias em módulos separados.'
            ),
            'texto': (
                'O módulo **cortex** controla o acesso à plataforma principal (Identidade, '
                'Organizacional, Pessoas Institucionais e Acadêmico).\n\n'
                '**Níveis (do menor ao maior):**\n'
                '1. **EDITAR_EU (L1 — Empregado):** lê e edita apenas recursos próprios; '
                'pode consultar catálogos de referência (setores, funções, cargos, cursos).\n'
                '2. **LER_TUDO (L2 — Gerente):** leitura ampla em pessoas, vínculos e empresas; '
                'não pode criar, alterar ou excluir recursos de terceiros.\n'
                '3. **EDITAR_TUDO (L3 — Master):** leitura e escrita em todos os recursos '
                '(staff, admin ou superusuário).\n\n'
                '**Derivação do nível:**\n'
                '- L3: `is_staff`, `is_admin` ou `is_superuser`.\n'
                '- L2: servidor ou terceirizado com perfil ativo.\n'
                '- L1: demais usuários (ex.: aluno).\n\n'
                '**Matriz de leitura:**\n'
                '- Catálogos (setores, funções, cargos, cursos): qualquer autenticado.\n'
                '- Pessoas e vínculos pessoais: L2+ vê todos; L1 vê só o próprio.\n'
                '- Empresas: L2+ vê todas; L1 não vê nenhuma.\n\n'
                '**Escrita:** apenas L3, exceto recursos do próprio usuário (ex.: atualizar '
                'próprio perfil, contatos e endereço).\n\n'
                'O payload `user.permissoes` no login/me retorna `{"cortex": "<nível>"}` e, '
                'quando aplicável, chaves adicionais por módulo (ex.: `infraestrutura` com flags booleanas).'
            ),
            'niveis': [
                {
                    'codigo': PERMISSAO_CORTEX_EDITAR_EU,
                    'ordem': NIVEL_CORTEX[PERMISSAO_CORTEX_EDITAR_EU],
                    'nome': 'Empregado',
                    'descricao': 'Acesso ao próprio registro e catálogos de referência.',
                },
                {
                    'codigo': PERMISSAO_CORTEX_LER_TUDO,
                    'ordem': NIVEL_CORTEX[PERMISSAO_CORTEX_LER_TUDO],
                    'nome': 'Gerente',
                    'descricao': 'Leitura ampla; escrita bloqueada exceto no próprio usuário.',
                },
                {
                    'codigo': PERMISSAO_CORTEX_EDITAR_TUDO,
                    'ordem': NIVEL_CORTEX[PERMISSAO_CORTEX_EDITAR_TUDO],
                    'nome': 'Master',
                    'descricao': 'Leitura e escrita totais na plataforma.',
                },
            ],
            'exemplos': [
                {
                    'perfil': 'Aluno',
                    'nivel': PERMISSAO_CORTEX_EDITAR_EU,
                    'pode': [
                        'ver e editar o próprio usuário',
                        'ver o próprio perfil de aluno e vínculos aluno-curso',
                        'listar catálogos (setores, funções, cargos, cursos)',
                    ],
                    'nao_pode': [
                        'listar outros usuários ou servidores',
                        'listar empresas',
                        'criar ou alterar setores, cursos ou vínculos de terceiros',
                    ],
                },
                {
                    'perfil': 'Servidor ativo',
                    'nivel': PERMISSAO_CORTEX_LER_TUDO,
                    'pode': [
                        'listar usuários, alunos, servidores e empresas',
                        'ler contatos de outros usuários (somente GET)',
                    ],
                    'nao_pode': [
                        'criar setores ou cursos',
                        'adicionar contato em nome de outro usuário',
                        'alterar dados de terceiros',
                    ],
                },
                {
                    'perfil': 'Staff ou administrador',
                    'nivel': PERMISSAO_CORTEX_EDITAR_TUDO,
                    'pode': [
                        'criar, alterar e desativar qualquer recurso da plataforma',
                    ],
                    'nao_pode': [],
                },
            ],
        }

    @classmethod
    def documentacao_infraestrutura(cls) -> dict:
        capacidades = [
            {
                'codigo': 'operar',
                'nome': 'Operar',
                'quem_usa': 'Responsável no balcão',
                'pode': (
                    'Realizar empréstimo, devolver itens, trocar titular; listar e filtrar '
                    'empréstimos de qualquer pessoa.'
                ),
                'nao_sem_capacidade': (
                    'Registrar operações de terceiros; ver histórico amplo de empréstimos.'
                ),
                'descricao': (
                    'Registrar retirada, devolução e troca de titular; consulta ampla de '
                    'empréstimos. Não confere elegibilidade ao solicitante.'
                ),
            },
            {
                'codigo': 'cadastrar',
                'nome': 'Cadastrar',
                'quem_usa': 'TI / gestão estrutural',
                'pode': (
                    'Criar, editar, desativar e reativar blocos, salas, recursos e vínculos '
                    'sala–setor; enviar e remover foto do recurso (POST/DELETE '
                    '/recursos/{pk}/foto/ ou campo foto no multipart do POST de criação).'
                ),
                'nao_sem_capacidade': 'Alterar cadastro estrutural.',
                'descricao': (
                    'Manutenção estrutural: blocos, salas, recursos e vínculos sala–setor, '
                    'incluindo upload e remoção da foto do recurso. Leitura JSON dos catálogos '
                    'permanece aberta a autenticados; o GET da foto do recurso é público '
                    '(proxy da API, bucket S3 privado).'
                ),
            },
            {
                'codigo': 'autorizar',
                'nome': 'Autorizar',
                'quem_usa': 'Coordenação / chefia',
                'pode': 'Listar, conceder, detalhar e revogar autorizações.',
                'nao_sem_capacidade': 'Gerir autorizações de retirada.',
                'descricao': (
                    'Conceder, listar, detalhar e revogar autorizações por sala ou recurso.'
                ),
            },
            {
                'codigo': 'retirada_irrestrita',
                'nome': 'Retirada irrestrita',
                'quem_usa': 'Solicitante (ex.: diretor)',
                'pode': (
                    'Ser elegível a qualquer recurso na retirada, sem autorização nem vínculo '
                    'setorial.'
                ),
                'nao_sem_capacidade': (
                    'Receber recurso apenas por autorização, perfil (servidor/terceirizado), '
                    'SalaSetor (chaves) ou outra regra automática.'
                ),
                'descricao': (
                    'Solicitante elegível a qualquer recurso sem autorização explícita. '
                    'Admin/superuser recebem esta flag no bypass de acesso total. '
                    'Complementa (não substitui) as regras automáticas de servidor e terceirizado.'
                ),
            },
        ]
        regras_automaticas = [
            {
                'codigo': 'acesso_total_admin',
                'nome': 'Acesso total (admin/superuser)',
                'descricao': (
                    'is_admin ou is_superuser compilam todas as capacidades como true. '
                    'is_staff sozinho não ativa esse bypass.'
                ),
            },
            {
                'codigo': 'servidor_ativo',
                'nome': 'Servidor ativo',
                'descricao': (
                    'Servidor ativo pode retirar qualquer recurso (chave, mídia ou material '
                    'didático), sem autorização e sem retirada_irrestrita na função.'
                ),
            },
            {
                'codigo': 'terceirizado_ativo',
                'nome': 'Terceirizado ativo',
                'descricao': (
                    'Terceirizado ativo pode retirar qualquer chave, sem autorização. '
                    'Para mídia ou material didático precisa de Autorizacao ou retirada_irrestrita.'
                ),
            },
            {
                'codigo': 'sala_setor',
                'nome': 'Vínculo setorial na sala',
                'descricao': (
                    'SetorVinculo ativo em setor ligado à sala (SalaSetor) libera chave '
                    'daquela sala ao solicitante.'
                ),
            },
            {
                'codigo': 'autorizacao_vigente',
                'nome': 'Autorização vigente',
                'descricao': (
                    'Autorização não revogada no período, no recurso ou na sala, libera o '
                    'recurso correspondente ao beneficiário.'
                ),
            },
        ]
        return {
            'chave': 'infraestrutura',
            'titulo': 'Infraestrutura',
            'resumo': (
                'Capacidades booleanas do módulo de liberação de recursos físicos '
                '(chaves, mídias e materiais didáticos), independentes do nível Cortex L1–L3. '
                'Inclui regras automáticas de elegibilidade do solicitante (servidor, '
                'terceirizado, SalaSetor, autorização e retirada irrestrita).'
            ),
            'texto': (
                'O módulo infraestrutura controla quem opera o balcão (guarda/auxiliar), quem '
                'cadastra a estrutura física, quem autoriza retiradas e quem pode solicitar '
                'recursos. As quatro capacidades no payload são booleanas e independentes dos '
                'níveis Cortex. Use o campo secoes para a documentação detalhada em blocos '
                'renderizáveis; capacidades, regras_automaticas e exemplos trazem a matriz '
                'estruturada.'
            ),
            'secoes': [
                {
                    'titulo': 'Compilação das capacidades (permissoes_infraestrutura)',
                    'itens': [
                        {
                            'destaque': 'Acesso total (bypass)',
                            'texto': (
                                'is_admin ou is_superuser recebem todas as capacidades ligadas '
                                '(operar, cadastrar, autorizar, retirada_irrestrita). is_staff '
                                'não entra nesse bypass (só afeta o nível Cortex L3).'
                            ),
                        },
                        {
                            'destaque': 'Demais usuários',
                            'texto': (
                                'União (OR) de: (1) flags de PermissaoFuncaoInfraestrutura das '
                                'funções dos SetorVinculo ativos (setor e função ativos); '
                                '(2) flags de PermissaoUsuarioInfraestrutura do próprio usuário. '
                                'Sem nenhuma das duas fontes, todas as flags ficam false.'
                            ),
                        },
                        {
                            'destaque': 'Payload típico',
                            'texto': (
                                '{"infraestrutura": {"operar": false, "cadastrar": false, '
                                '"autorizar": false, "retirada_irrestrita": false}}'
                            ),
                        },
                    ],
                },
                {
                    'titulo': 'Leitura e consulta na API',
                    'paragrafos': [
                        (
                            'Leitura de catálogos (blocos, salas, recursos) em JSON: qualquer '
                            'usuário autenticado (GET listagem e detalhe). Escrita exige '
                            'cadastrar.'
                        ),
                        (
                            'GET /recursos/{pk}/foto/ é público (AllowAny): serve o arquivo via '
                            'proxy da API; o bucket S3 permanece privado. Upload e remoção da '
                            'foto exigem cadastrar (POST/DELETE no mesmo path ou campo foto no '
                            'POST de criação do recurso).'
                        ),
                        (
                            'Consulta de empréstimos sem operar (L1 do módulo): só empréstimos '
                            'ativos em que o usuário é o solicitante; sem histórico concluído e '
                            'sem filtros de terceiros.'
                        ),
                    ],
                },
                {
                    'titulo': 'Elegibilidade do solicitante (quem pode receber o recurso)',
                    'introducao': (
                        'Independente de quem opera o balcão. Avaliada em ordem em '
                        'EmprestimoHelpers.solicitante_pode_retirar_recurso:'
                    ),
                    'itens': [
                        {
                            'ordem': 1,
                            'destaque': 'retirada_irrestrita',
                            'texto': (
                                'No payload do solicitante: qualquer recurso (chave, mídia ou '
                                'material didático).'
                            ),
                        },
                        {
                            'ordem': 2,
                            'destaque': 'Servidor ativo',
                            'texto': (
                                'Servidor ativo pode retirar qualquer recurso (chave, mídia ou '
                                'material didático), sem autorização explícita.'
                            ),
                        },
                        {
                            'ordem': 3,
                            'destaque': 'Terceirizado ativo',
                            'texto': (
                                'Terceirizado ativo pode retirar qualquer chave. Não vale para '
                                'mídia ou material didático (precisa Autorizacao ou '
                                'retirada_irrestrita).'
                            ),
                        },
                        {
                            'ordem': 4,
                            'destaque': 'SalaSetor',
                            'texto': (
                                'Solicitante com vínculo setorial ativo em setor ligado à sala da '
                                'chave: pode retirar chave dessa sala.'
                            ),
                        },
                        {
                            'ordem': 5,
                            'destaque': 'Autorizacao vigente',
                            'texto': (
                                'Autorização não revogada, dentro do período, no recurso ou na '
                                'sala do recurso. Autorização por sala cobre recursos futuros da '
                                'mesma sala.'
                            ),
                        },
                    ],
                    'observacoes': [
                        'Se nenhuma regra passar, o solicitante não pode receber aquele recurso.',
                        (
                            'retirada_irrestrita, servidor/terceirizado, SalaSetor e autorização '
                            'definem quem recebe; operar define quem registra a operação. Um '
                            'guarda com operar ainda só libera o recurso se o solicitante for '
                            'elegível.'
                        ),
                    ],
                },
                {
                    'titulo': 'Relação com níveis Cortex (orientação típica)',
                    'itens': [
                        {
                            'destaque': 'L1 (EDITAR_EU)',
                            'texto': (
                                'Em geral sem capacidades; só consulta empréstimos ativos '
                                'próprios; pode ser solicitante se tiver autorização, SalaSetor, '
                                'perfil de servidor/terceirizado (conforme o tipo do recurso) ou '
                                'retirada_irrestrita.'
                            ),
                        },
                        {
                            'destaque': 'L2 (LER_TUDO)',
                            'texto': 'Tipicamente operar (guardas/auxiliares).',
                        },
                        {
                            'destaque': 'L3 (EDITAR_TUDO)',
                            'texto': (
                                'Tipicamente autorizar/cadastrar conforme a função; admin e '
                                'superuser têm acesso total às quatro capacidades.'
                            ),
                        },
                    ],
                    'paragrafos': [
                        (
                            'Os níveis Cortex não substituem as flags de Infraestrutura: a '
                            'checagem nas views usa usuario_pode_operar, usuario_pode_cadastrar '
                            'e usuario_pode_autorizar_infraestrutura.'
                        ),
                    ],
                },
            ],
            'capacidades': capacidades,
            'regras_automaticas': regras_automaticas,
            'exemplos': [
                {
                    'perfil': 'Aluno sem vínculo setorial nem autorização',
                    'capacidades': {
                        'operar': False,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'consultar empréstimos ativos no próprio nome',
                        'listar blocos, salas e recursos (somente leitura)',
                    ],
                    'nao_pode': [
                        'receber chave/recurso (não elegível)',
                        'registrar empréstimos de terceiros',
                        'cadastrar estrutura',
                        'conceder autorizações',
                        'ver histórico de empréstimos concluídos',
                    ],
                },
                {
                    'perfil': 'Guarda com função só operar',
                    'capacidades': {
                        'operar': True,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'emprestar, devolver e trocar titular (se o solicitante for elegível)',
                        'consultar empréstimos com filtros amplos',
                    ],
                    'nao_pode': [
                        'cadastrar blocos, salas ou recursos',
                        'conceder ou revogar autorizações',
                        'retirar recurso no próprio nome só por ter operar (precisa elegibilidade)',
                    ],
                },
                {
                    'perfil': 'Terceirizado ativo',
                    'capacidades': {
                        'operar': False,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'receber qualquer chave como solicitante (regra automática por perfil)',
                        'consultar empréstimos ativos no próprio nome',
                    ],
                    'nao_pode': [
                        'receber mídia ou material didático só por ser terceirizado '
                        '(precisa autorização ou retirada_irrestrita)',
                        'operar o balcão',
                        'cadastrar ou autorizar',
                    ],
                },
                {
                    'perfil': 'Servidor ativo (sem autorização explícita)',
                    'capacidades': {
                        'operar': False,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'receber qualquer recurso (chave, mídia ou material didático) como solicitante',
                    ],
                    'nao_pode': [
                        'operar o balcão só por ser servidor',
                        'cadastrar ou autorizar',
                    ],
                },
                {
                    'perfil': 'Usuário com vínculo no setor da sala (sem perfil servidor/terceirizado)',
                    'capacidades': {
                        'operar': False,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'receber chave da sala cujo setor está em SalaSetor e no seu SetorVinculo',
                    ],
                    'nao_pode': [
                        'receber chave de sala de outro setor sem autorização',
                        'receber mídia/material didático só pelo vínculo setorial',
                    ],
                },
                {
                    'perfil': 'Coordenador com função completa',
                    'capacidades': {
                        'operar': True,
                        'cadastrar': True,
                        'autorizar': True,
                        'retirada_irrestrita': True,
                    },
                    'pode': [
                        'operar empréstimos',
                        'cadastrar estrutura física',
                        'conceder e revogar autorizações',
                        'receber qualquer recurso como solicitante (retirada_irrestrita)',
                    ],
                    'nao_pode': [],
                },
                {
                    'perfil': 'Administrador ou superusuário',
                    'capacidades': {
                        'operar': True,
                        'cadastrar': True,
                        'autorizar': True,
                        'retirada_irrestrita': True,
                    },
                    'pode': [
                        'todas as operações do módulo (bypass de acesso total na compilação)',
                    ],
                    'nao_pode': [],
                },
            ],
        }
