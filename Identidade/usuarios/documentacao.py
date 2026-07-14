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
                'Capacidades operacionais do módulo de liberação de recursos físicos '
                '(chaves, mídias e materiais didáticos), independentes do nível Cortex L1–L3.'
            ),
            'texto': (
                'O módulo **infraestrutura** expõe quatro capacidades booleanas compiladas a partir '
                'das funções dos vínculos setoriais ativos do usuário (`SetorVinculo` com setor e '
                'função ativos). Quando o usuário possui mais de um vínculo, aplica-se a **união (OR)** '
                'das flags configuradas em `PermissaoFuncaoInfraestrutura`.\n\n'
                '**Capacidades:**\n'
                '- `operar`: retirada, devolução, troca de titular e consulta ampla de empréstimos.\n'
                '- `cadastrar`: blocos, salas, recursos e vínculos sala–setor.\n'
                '- `autorizar`: conceder e revogar autorizações de retirada.\n'
                '- `retirada_irrestrita`: solicitar qualquer recurso sem autorização explícita '
                '(tipicamente diretores, coordenadores e chefes, conforme configuração da função).\n\n'
                '**Relação com níveis Cortex:**\n'
                '- L1 (EDITAR_EU): em geral sem capacidades; consulta apenas empréstimos ativos próprios.\n'
                '- L2 (LER_TUDO): tipicamente `operar` para guardas e auxiliares.\n'
                '- L3 (EDITAR_TUDO): pode combinar `autorizar` e `cadastrar`, conforme a função.\n\n'
                'O payload retorna `{"infraestrutura": {"operar": false, "cadastrar": false, '
                '"autorizar": false, "retirada_irrestrita": false}}` quando não há capacidade alguma.'
            ),
            'capacidades': [
                {
                    'codigo': 'operar',
                    'nome': 'Operar',
                    'descricao': 'Fluxo operacional de empréstimos e consulta ampla.',
                },
                {
                    'codigo': 'cadastrar',
                    'nome': 'Cadastrar',
                    'descricao': 'Manutenção estrutural de blocos, salas e recursos.',
                },
                {
                    'codigo': 'autorizar',
                    'nome': 'Autorizar',
                    'descricao': 'Conceder e revogar autorizações por sala ou recurso.',
                },
                {
                    'codigo': 'retirada_irrestrita',
                    'nome': 'Retirada irrestrita',
                    'descricao': 'Retirar recursos sem autorização explícita adicional.',
                },
            ],
            'exemplos': [
                {
                    'perfil': 'Aluno sem vínculo setorial com permissão',
                    'capacidades': {
                        'operar': False,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'consultar empréstimos ativos no próprio nome (via regras do módulo)',
                    ],
                    'nao_pode': [
                        'operar retiradas de terceiros',
                        'cadastrar recursos',
                        'conceder autorizações',
                    ],
                },
                {
                    'perfil': 'Guarda com função configurada',
                    'capacidades': {
                        'operar': True,
                        'cadastrar': False,
                        'autorizar': False,
                        'retirada_irrestrita': False,
                    },
                    'pode': [
                        'emprestar, devolver e trocar titular',
                        'consultar empréstimos com filtros amplos',
                    ],
                    'nao_pode': [
                        'cadastrar blocos ou salas',
                        'conceder autorizações',
                    ],
                },
                {
                    'perfil': 'Coordenador com função configurada',
                    'capacidades': {
                        'operar': True,
                        'cadastrar': True,
                        'autorizar': True,
                        'retirada_irrestrita': True,
                    },
                    'pode': [
                        'operar empréstimos',
                        'cadastrar estrutura física',
                        'autorizar retiradas',
                        'retirar recursos sem autorização explícita',
                    ],
                    'nao_pode': [],
                },
            ],
        }
