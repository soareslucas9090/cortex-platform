# Diretrizes do Domínio: Acadêmico

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Acadêmico** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Academico` gerencia **alunos**, **cursos** e **vínculos aluno–curso** (`AlunoCurso`).

**Monitoria** e funções em setor acadêmico pertencem ao domínio **Organizacional** (`Funcao` + `SetorVinculo`, em geral com `exige_aluno=True`) — não implementar monitoria como entidade no Acadêmico.

### Modelos e Relacionamentos

- **Aluno**: herança 1:1 com `Usuario`; situação e forma de ingresso; campos de transporte (somente leitura de regra de escrita — ver abaixo).
- **Curso**: catálogo de cursos ofertados; relação **N:1** com **Setor** (`Organizacional`).
- **AlunoCurso**: associação aluno ↔ curso; **`matricula` opcional com unicidade global** quando preenchida; campo **`ativo`** no vínculo.

### `Curso.nivel_ensino` e `Curso.modalidade` (AC.1)

**`nivel_ensino`** está no model. `IntegerChoices` **`NivelEnsino`**:

| Valor | Rótulo |
|------:|--------|
| 1 | Ensino Médio |
| 2 | Técnico |
| 3 | Superior |
| 4 | Pós-graduação |
| 5 | Formação profissional |
| 6 | Mestrado |
| 7 | Preparatório vestibular |

**`modalidade`** é opcional (`null=True`). `IntegerChoices` **`Modalidade`**: FIC, Qualificação Profissional, Curso Livre, modalidades técnicas (integrado, EJA, subsequente e variantes EaD), Licenciatura, Bacharelado, Tecnologia, Especialização e Mestrado (inteiros 1–13 conforme `Academico/cursos/choices.py`).

O campo **`nivel_ensino`** aceita nulo: **nulo significa não classificado** e não é Ensino Médio. Cursos já gravados, inclusive o seed, permanecem com `nivel_ensino` e `modalidade` nulos até edição explícita ou importação com valores válidos na planilha — a carga **não** infere nível ou modalidade pelo nome do curso. Criação pela API exige um inteiro de **`NivelEnsino`**; **`modalidade`** é opcional na API. Elegibilidade de solicitação na portaria EM usará `nivel_ensino=ENSINO_MEDIO`.

### Fronteira com AcessoCampus (**planejado**)

- **Academico** define catálogo e elegibilidade acadêmica (nível de ensino do curso, matrícula, situação do aluno, `AlunoCurso.ativo`).
- **AcessoCampus** possuirá solicitações, programações, eventos materializados e registros de portaria — **não** colocar models de circulação/portaria no Academico.

### Estrutura de Apps

```text
Academico/
├── __init__.py
├── urls.py
├── alunos/          # Aluno
├── cursos/          # Curso
└── aluno_cursos/    # AlunoCurso
```

---

## Prefixo HTTP

**`/cortex/academico/`**

---

## Regras Específicas do Domínio

### Herança do model `Aluno`

**OneToOneField com `primary_key=True`** para `Usuario`, mesmo padrão de Servidor/Terceirizado.

### Choices (valores inteiros no código)

Persistidos como **`IntegerField`** com `IntegerChoices`:

**Situação do aluno** (`SituacaoAluno`):

| Constante | Valor | Rótulo |
| --------- | ----- | ------ |
| `MATRICULADO` | 1 | Matriculado |
| `TRANCADO` | 2 | Trancado |
| `FORMADO` | 3 | Formado |
| `DESISTENTE` | 4 | Desistente |
| `TRANSFERIDO` | 5 | Transferido |

**Forma de ingresso** (`FormaIngresso`):

| Constante | Valor | Rótulo |
| --------- | ----- | ------ |
| `VESTIBULAR` | 1 | Vestibular |
| `ENEM` | 2 | ENEM |
| `TRANSFERENCIA` | 3 | Transferência |
| `REINGRESSO` | 4 | Reingresso |

### `Curso` e `Setor`

No banco, `Curso.setor` é **nullable** (`null=True`, `blank=True`) por compatibilidade de schema; na **regra de negócio**, todo curso **deve** ter setor.

- **Criar** curso (API ou importação): `setor` / `setor_id` **obrigatório** — não é permitido criar sem setor.
- **Editar** curso: **não** é permitido remover o setor (PATCH que deixaria o curso sem setor é rejeitado).
- **Importação de usuários** (aba `Curso`): cria ou atualiza cursos por `codigo_curso` normalizado (caixa, acentos e espaços); `setor_id` obrigatório em cada linha — o setor pode ter sido criado na fase de catálogo da mesma importação (ver `docs/schema/importacao-usuarios.md`). `nivel_ensino` e `modalidade` são lidos, normalizados para as choices e gravados na criação e na atualização; célula vazia persiste nulo; valor inválido gera erro de linha.
- **Cursos legados** (data migration `cursos.0004`): associa o setor de cada curso semeado conforme as abas `Curso`/`Setor` de `docs/seeds/import/modelo-importacao-usuarios.ods`. A migration **nunca aborta o deploy**: sigla de setor ausente no banco gera apenas log de aviso e o curso permanece com `setor` NULL; só cursos ainda sem setor são atualizados (associação existente nunca é sobrescrita). Curso legado com `setor` NULL precisa receber setor para ser editado (PATCH). O curso `14JOPC` não consta no `.ods` atual, mas é preservado (setor `DEPENTE`) por já existir em bancos implantados.

### `AlunoCurso.matricula`

Constraint `aluno_cursos_matricula_unica`: matrícula **única em todo o sistema** quando informada (mesma regra de unicidade global descrita em Identidade para login).

### Campos sincronizados pelo Transporte

No model `Aluno`, estes campos refletem strikes/bloqueio do transporte universitário:

- `faltas`
- `is_bloqueado`
- `quantidade_bloqueios`

Atualizados por **`Transporte.strikes.helpers.sincronizar_faltas_transporte`** (e fluxos de strike/ticket). **Não** reimplementar lógica de bloqueio ou contagem de faltas no Acadêmico; alterações passam pelo domínio Transporte.

---

## Permissões HTTP (ADR-002)

| Recurso | Leitura | Escrita |
| ------- | ------- | ------- |
| **Cursos** | Autenticado (catálogo) | L3 |
| **Alunos**, **AlunoCurso** | `IsOwnerOrAdminMixin`: L2+ todos; L1 próprio | L3 |

---

## Endpoints principais

Paths relativos a `/cortex/academico/`.

### Cursos

| Método | Path |
| ------ | ---- |
| GET, POST | `cursos/` |
| GET, PATCH | `cursos/{pk}/` |
| POST | `cursos/{pk}/desativar/`, `cursos/{pk}/reativar/` |

**Listagem** (`GET cursos/`): filtros opcionais por query param `setor_id`, `nivel_ensino` e `modalidade`. Os query params apenas reduzem o conjunto de resultados — nunca expandem o acesso.

### Alunos

| Método | Path |
| ------ | ---- |
| GET, POST | `alunos/` |
| GET, PATCH | `alunos/{usuario_id}/` |

(O detalhe usa **`usuario_id`**, não PK separada — aluno PK = usuário.)

### Aluno–curso

| Método | Path |
| ------ | ---- |
| GET, POST | `aluno-cursos/` |
| GET, PATCH | `aluno-cursos/{pk}/` |
| POST | `aluno-cursos/{pk}/encerrar/` |

---

## O que NÃO fazer

- **Não** criar, importar ou editar um curso sem setor associado.
- **Não** criar entidade ou API de **monitoria** aqui — use Organizacional.
- **Não** alterar `faltas` / `is_bloqueado` / `quantidade_bloqueios` em business de Aluno sem coordenar com Transporte.
- **Não** inventar endpoints fora dos `urls.py` existentes.
- **Não** tratar choices como strings na API persistida sem alinhar aos inteiros do model.
- **Não** inferir Ensino Médio pelo nome do curso — usar **`nivel_ensino`**. Nulo não é Ensino Médio.
- **Não** implementar fluxo de circulação/portaria (solicitação, eventos, registro na guarita) no Academico — bounded context **AcessoCampus** ([domains/acesso-campus.md](acesso-campus.md), ADR-003).
