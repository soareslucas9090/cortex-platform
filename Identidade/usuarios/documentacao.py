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
        return {
            'chave': 'infraestrutura',
            'titulo': 'Infraestrutura',
            'resumo': (
                'Capacidades booleanas do módulo de liberação de recursos físicos '
                '(chaves, mídias e materiais didáticos), independentes do nível Cortex L1–L3. '
                'Inclui regras automáticas de elegibilidade do solicitante (limpeza, SalaSetor, '
                'autorização e retirada irrestrita).'
            ),
            'texto': (
                'O módulo **infraestrutura** controla quem **opera** o balcão (guarda/auxiliar), '
                'quem **cadastra** a estrutura física, quem **autoriza** retiradas e quem pode '
                '**solicitar** recursos. As quatro capacidades no payload são booleanas e '
                'independentes dos níveis Cortex.\n\n'
                '---\n\n'
                '## Compilação das capacidades (`permissoes_infraestrutura`)\n\n'
                '1. **Acesso total (bypass):** `is_admin` ou `is_superuser` recebem todas as '
                'capacidades ligadas (`operar`, `cadastrar`, `autorizar`, `retirada_irrestrita`). '
                '`is_staff` **não** entra nesse bypass (só afeta o nível Cortex L3).\n'
                '2. **Demais usuários:** união (**OR**) das flags de `PermissaoFuncaoInfraestrutura` '
                'das funções dos `SetorVinculo` ativos (setor e função ativos). Sem vínculo com '
                'função configurada → todas as flags `false`.\n'
                '3. Payload típico: '
                '`{"infraestrutura": {"operar": false, "cadastrar": false, "autorizar": false, '
                '"retirada_irrestrita": false}}`.\n\n'
                '---\n\n'
                '## Capacidades e o que liberam na API\n\n'
                '| Capacidade | Quem usa | Pode | Não pode (sem a flag) |\n'
                '|---|---|---|---|\n'
                '| `operar` | Responsável no balcão | Realizar empréstimo, devolver itens, '
                'trocar titular; listar/filtrar empréstimos de qualquer pessoa | Registrar '
                'operações de terceiros; ver histórico amplo |\n'
                '| `cadastrar` | TI / gestão estrutural | Criar/editar/desativar/reativar blocos, '
                'salas, recursos e vínculos sala–setor | Alterar cadastro estrutural |\n'
                '| `autorizar` | Coordenação / chefia | Listar, conceder, detalhar e revogar '
                'autorizações | Gerir autorizações |\n'
                '| `retirada_irrestrita` | Solicitante (ex.: diretor) | Ser elegível a **qualquer** '
                'recurso na retirada, sem autorização nem vínculo setorial | — (só afeta elegibilidade '
                'do solicitante, não opera o balcão sozinha) |\n\n'
                '**Leitura de catálogos** (blocos, salas, recursos): qualquer usuário autenticado '
                '(GET). Escrita exige `cadastrar`.\n\n'
                '**Consulta de empréstimos sem `operar` (L1 do módulo):** só empréstimos **ativos** '
                'em que o usuário é o **solicitante**; sem histórico concluído e sem filtros de '
                'terceiros.\n\n'
                '---\n\n'
                '## Elegibilidade do solicitante (quem pode receber o recurso)\n\n'
                'Independente de quem opera o balcão. Avaliada em ordem em '
                '`EmprestimoHelpers.solicitante_pode_retirar_recurso`:\n\n'
                '1. **`retirada_irrestrita`** no payload do solicitante → qualquer recurso '
                '(chave, mídia ou material didático).\n'
                '2. **Servente de limpeza** → terceirizado **ativo** com cargo ativo de nome '
                'exato **SERVENTE DE LIMPEZA** → pode retirar **qualquer chave** '
                '(não vale para mídia/material didático). Não depende de flag em '
                '`PermissaoFuncaoInfraestrutura`; é regra automática por cargo.\n'
                '3. **`SalaSetor`** → solicitante com vínculo setorial ativo em setor ligado à '
                'sala da chave → pode retirar **chave** dessa sala.\n'
                '4. **`Autorizacao` vigente** → autorização não revogada, dentro do período, '
                'no recurso ou na sala do recurso (autorização por sala cobre recursos futuros '
                'da mesma sala).\n\n'
                'Se nenhuma regra passar → solicitante **não** pode receber aquele recurso.\n\n'
                '**Importante:** `retirada_irrestrita` e limpeza/SalaSetor/autorização definem '
                'quem **recebe**; `operar` define quem **registra** a operação. Um guarda com '
                '`operar` ainda só libera o recurso se o solicitante for elegível.\n\n'
                '---\n\n'
                '## Relação com níveis Cortex (orientação típica)\n\n'
                '- **L1 (EDITAR_EU):** em geral sem capacidades; só consulta empréstimos ativos '
                'próprios; pode ser solicitante se tiver autorização, SalaSetor ou for limpeza.\n'
                '- **L2 (LER_TUDO):** tipicamente `operar` (guardas/auxiliares).\n'
                '- **L3 (EDITAR_TUDO):** tipicamente `autorizar`/`cadastrar` conforme a função; '
                'admin/superuser têm acesso total às quatro capacidades.\n\n'
                'Os níveis Cortex **não** substituem as flags de Infraestrutura: a checagem nas '
                'views usa `usuario_pode_operar/cadastrar/autorizar_infraestrutura`.'
            ),
            'capacidades': [
                {
                    'codigo': 'operar',
                    'nome': 'Operar',
                    'descricao': (
                        'Registrar retirada, devolução e troca de titular; consulta ampla de '
                        'empréstimos. Não confere elegibilidade ao solicitante.'
                    ),
                },
                {
                    'codigo': 'cadastrar',
                    'nome': 'Cadastrar',
                    'descricao': (
                        'Manutenção estrutural: blocos, salas, recursos e vínculos sala–setor. '
                        'Leitura dos catálogos permanece aberta a autenticados.'
                    ),
                },
                {
                    'codigo': 'autorizar',
                    'nome': 'Autorizar',
                    'descricao': (
                        'Conceder, listar, detalhar e revogar autorizações por sala ou recurso.'
                    ),
                },
                {
                    'codigo': 'retirada_irrestrita',
                    'nome': 'Retirada irrestrita',
                    'descricao': (
                        'Solicitante elegível a qualquer recurso sem autorização explícita. '
                        'Admin/superuser recebem esta flag no bypass de acesso total. '
                        'Não substitui a regra automática do cargo SERVENTE DE LIMPEZA.'
                    ),
                },
            ],
            'regras_automaticas': [
                {
                    'codigo': 'acesso_total_admin',
                    'nome': 'Acesso total (admin/superuser)',
                    'descricao': (
                        'is_admin ou is_superuser compilam todas as capacidades como true. '
                        'is_staff sozinho não ativa esse bypass.'
                    ),
                },
                {
                    'codigo': 'servente_limpeza',
                    'nome': 'Servente de limpeza',
                    'descricao': (
                        'Terceirizado ativo com cargo SERVENTE DE LIMPEZA pode retirar qualquer '
                        'chave, sem autorização e sem retirada_irrestrita na função.'
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
            ],
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
                    'perfil': 'Servente de limpeza (terceirizado, cargo SERVENTE DE LIMPEZA)',
                    'capacidades': {
                        'operar': False,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'receber qualquer chave como solicitante (regra automática por cargo)',
                        'consultar empréstimos ativos no próprio nome',
                    ],
                    'nao_pode': [
                        'receber mídia ou material didático só por ser limpeza '
                        '(precisa autorização ou retirada_irrestrita)',
                        'operar o balcão',
                        'cadastrar ou autorizar',
                    ],
                },
                {
                    'perfil': 'Servidor com vínculo no setor da sala (sem autorização explícita)',
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
