# Visão Geral do Produto e do Sistema

## Objetivo

Este documento apresenta uma visão geral do Cortex como produto e como sistema **no estado atual**, consolidando:

- o propósito da aplicação;
- os principais conceitos de domínio implementados;
- a estratégia arquitetural adotada;
- a organização técnica do backend em produção de desenvolvimento.

Ele funciona como documento de entrada para quem precisa entender rapidamente:

- o que o sistema resolve;
- como ele está organizado;
- quais fundamentos técnicos sustentam a API.

---

## Visão geral do produto

O Cortex é um backend modular para operação de um contexto institucional e acadêmico, cobrindo:

- **identidade** de usuários (cadastro, contato, endereço, importação em lote);
- **estrutura organizacional** (setores, funções, vínculos);
- **pessoas institucionais** (servidores, cargos, terceirizados, empresas);
- **perfil acadêmico** (alunos, cursos, matrículas por curso);
- **infraestrutura** física e operacional (blocos, salas, recursos, empréstimos, autorizações — substituto funcional dos fluxos legados Chameco/Sigec na v1);
- **transporte universitário** (percursos, rotas, execuções, tickets, strikes, calendário operacional, bloqueios).

O núcleo permanece a entidade `Usuario`, sobre a qual perfis e vínculos se especializam.

---

## Problema que o sistema resolve

O sistema representa de forma consistente:

- quem são os usuários e como autenticam;
- quais perfis institucionais e acadêmicos possuem;
- como se vinculam a setores e funções;
- como espaços e recursos são emprestados e autorizados;
- como o transporte universitário reserva vagas, registra faltas e bloqueios.

Conceitos próximos permanecem separados, por exemplo:

- `Cargo` (catálogo institucional) e `Funcao` (papel no setor);
- perfil acadêmico (`Aluno`, `AlunoCurso`) e atuação organizacional (`SetorVinculo`);
- identidade base (`Usuario`) e especializações em outros domínios.

---

## Visão geral do domínio

O sistema está dividido em **seis domínios** de negócio, cada um um módulo agregador na raiz do repositório:

### `Identidade`

- `Usuario`, `Contato`, `Endereco`
- `ImportacaoLote` (importação de usuários em `Identidade.usuarios`)
- **Não** existe app `matriculas`: matrícula é atributo em `Servidor`, `Terceirizado` e `AlunoCurso`

### `Organizacional`

- `Setor`, `Funcao`, `SetorVinculo`

### `PessoasInstitucionais`

- `Servidor`, `Cargo`, `Terceirizado`, `EmpresaInstituicao`
- Não há entidade `Estagiario` no código atual

### `Academico`

- `Aluno`, `Curso`, `AlunoCurso`

### `Infraestrutura`

- `Bloco`, `Sala`, `SalaSetor`, `Recurso`, permissões por função/usuário, `Autorizacao`, `Emprestimo`, `ItemEmprestimo`, `ImportacaoLote` (carga de infraestrutura)

### `Transporte`

- Doze apps em `PROJECT_APPS` (percursos, rotas, motoristas, calendário, execuções, tickets, strikes, justificativas, relatórios, permissões, entradas sem ticket, bloqueios)

Mapa detalhado: `02-bounded-contexts.md`. Regras por módulo: `docs/domains/` (incluindo `infraestrutura.md`). Contexto de produto de Infraestrutura: `docs/schema/infraestrutura.md`.

---

## Conceitos centrais consolidados

### `Usuario` como centro da identidade

`AUTH_USER_MODEL = usuarios.Usuario`. Campos relevantes: `email` e `cpf` (ambos `unique`, nullable), `usuario_coletivo` e pools M2M (`empresas_coletivo`, `cargos_coletivo`, `funcoes_coletivo`, `setores_coletivo`) para contas compartilhadas.

### Autenticação híbrida

Login via `EmailOrCpfBackend` (`AppCore.basics.auth.backends`): identificador `login` como **e-mail**, **CPF** (11 dígitos) ou **matrícula ativa** em `AlunoCurso`, `Servidor` ou `Terceirizado`. Após localizar o usuário, exige CPF cadastrado ou matrícula válida para permitir autenticação.

Rotas de autenticação: `/cortex/auth/`.

### `Cargo` e `Funcao` são conceitos diferentes

- **`Cargo`**: catálogo de posição formal; **obrigatório** em `Servidor`; pode ser referenciado **opcionalmente** em `Terceirizado` (`FK` com `SET_NULL`).
- **`Funcao`**: papel no vínculo com setor (`papel_funcao`, `categoria`, `descricao`, `e_gratificada`, `exige_aluno`, `ativo`).

### `SetorVinculo` é entidade de negócio

Relaciona `usuario`, `setor`, `funcao` e `responsavel` — não é apenas tabela associativa.

### Monitoria é função

Monitor é registro em `Funcao`, não atributo booleano em `SetorVinculo`.

### Permissões transversais

Níveis Cortex L1–L3 (ADR-002) compilados em `user.permissoes['cortex']`. Módulos Infraestrutura e Transporte adicionam capacidades próprias (booleanas), independentes da hierarquia L1–L3 onde aplicável.

### Aluno e transporte

`Aluno` mantém `faltas`, `is_bloqueado` e `quantidade_bloqueios`, sincronizados pelo domínio Transporte.

---

## Estratégia arquitetural

### 1. Modularização por domínio

Organização por contexto de negócio (ADR-001), com módulos PascalCase e apps internos em minúsculo.

### 2. Arquitetura em camadas

Por app: `models`, `business`, `rules`, `helpers`, `serializers`, `views`, `urls`.

### 3. Views leves

Validação via serializer; lógica em `business` / `rules`.

### 4. Base reutilizável em uso

- `AppCore/` — mixins, auth, storage, convenções
- `Auth/` — fluxos de autenticação da API
- `Cortex/` — settings, `PROJECT_APPS`, `urls` raiz, Celery Beat

### 5. Geração operacional de transporte

Celery Beat executa `gerar_execucoes_rotas_automaticas_task` a cada 5 minutos (`Cortex/settings.py`), alinhada ao calendário operacional.

---

## Estrutura do sistema

### Módulos de domínio (apps em `PROJECT_APPS`)

| Módulo | Prefixo HTTP |
|--------|----------------|
| `Identidade` | `/cortex/identidade/` |
| `Organizacional` | `/cortex/organizacional/` |
| `PessoasInstitucionais` | `/cortex/pessoas-institucionais/` |
| `Academico` | `/cortex/academico/` |
| `Infraestrutura` | `/cortex/infraestrutura/` |
| `Transporte` | `/cortex/transporte/` |

Além disso: `/cortex/auth/`, `/cortex/admin/`, schema OpenAPI em `/cortex/api/schema/`.

Alguns apps existem em `INSTALLED_APPS` sem `urls` no agregador do domínio (ex.: permissões de Infraestrutura e parte dos apps de Transporte). Ver `02-bounded-contexts.md`.

---

## Ordem de implementação (histórico)

A sequência abaixo reflete marcos **já concluídos**, não roadmap futuro:

| Fase | Conteúdo |
|------|----------|
| M0–base | `AppCore`, `Auth`, `Cortex`, autenticação e convenções |
| M1 | Identidade (`usuarios`, `contatos`, `enderecos`) |
| M2 | Organizacional |
| M3 | PessoasInstitucionais |
| M4 | Acadêmico |
| M5 | Integração e consolidação entre os quatro primeiros domínios |
| — | Importação de usuários (`ImportacaoLote` em Identidade) |
| — | Infraestrutura v1 (blocos, salas, recursos, empréstimos, autorizações, importações) |
| — | Transporte (12 apps, permissões, relatórios, bloqueios, calendário, task Beat) |

Detalhes de planejamento: `docs/planning/master-implementation-plan.md` e milestones M1–M5.

---

## Regras importantes já conhecidas

- login por e-mail, CPF ou matrícula ativa;
- `Cargo` obrigatório para `Servidor`; opcional para `Terceirizado`;
- `EmpresaInstituicao` usada para terceirizados;
- todo vínculo com setor deve ter função (regra de domínio; model permite `funcao` nullable — validação em camadas superiores);
- um usuário pode ter múltiplos vínculos com setores;
- monitoria via `Funcao` no Organizacional;
- aluno monitor deve ter vínculo de setor quando exigido por `Funcao.exige_aluno`;
- reservas de sala fora do escopo da v1 de Infraestrutura.

---

## Documentos que detalham esta visão

- `docs/diagrams/02-bounded-contexts.md`
- `docs/diagrams/03-core-erd.md`
- `docs/diagrams/04-aggregates-and-invariants.md`
- `docs/decisions/ADR-001-modularizacao-por-dominio.md`
- `docs/decisions/ADR-002-permissoes-cortex-niveis.md`
- `docs/project/django-project-tree.md`
- `docs/domains/*` (incluindo `docs/domains/infraestrutura.md`)
- `docs/schema/infraestrutura.md` (contexto de produto de Infraestrutura)

---

## Próximo passo (manutenção)

Manter **documentação e código alinhados** após cada mudança estrutural. Tarefas operacionais e revisões pontuais estão em `docs/planning/followup-*` (por exemplo revisão pré-produção e fotos S3).

---

## O que este documento não tenta fazer

Não lista todos os atributos, endpoints ou regras finas — isso está em `docs/domains/`, schemas de API e no código.

---

## Resumo executivo

O Cortex é um backend modular com **seis domínios** implementados, `Usuario` no centro, autenticação híbrida e rotas sob `/cortex/<dominio>/`. Infraestrutura e Transporte estendem o núcleo identidade–organizacional–institucional–acadêmico. A base `AppCore` já está em uso; a evolução contínua prioriza coerência entre código, ADRs e esta documentação estrutural.
