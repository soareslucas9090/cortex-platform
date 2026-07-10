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
                'Outros produtos (ex.: Sigec) podem definir níveis próprios em módulos separados.'
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
                'O payload `user.permissoes` no login/me retorna `{"cortex": "<nível>"}`. '
                'Módulos futuros (ex.: Sigec) aparecerão como chaves adicionais nesse objeto.'
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
