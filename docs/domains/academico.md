# Diretrizes do Domínio: Acadêmico

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Acadêmico** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Academico` gerencia **alunos**, **cursos** e **vínculos aluno–curso** (`AlunoCurso`).

**Monitoria** e funções em setor acadêmico pertencem ao domínio **Organizacional** (`Funcao` + `SetorVinculo`, em geral com `exige_aluno=True`) — não implementar monitoria como entidade no Acadêmico.

### Modelos e Relacionamentos

- **Aluno**: herança 1:1 com `Usuario`; situação e forma de ingresso; campos de transporte (somente leitura de regra de escrita — ver abaixo).
- **Curso**: catálogo de cursos ofertados.
- **AlunoCurso**: associação aluno ↔ curso; **`matricula` opcional com unicidade global** quando preenchida.

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

- **Não** criar entidade ou API de **monitoria** aqui — use Organizacional.
- **Não** alterar `faltas` / `is_bloqueado` / `quantidade_bloqueios` em business de Aluno sem coordenar com Transporte.
- **Não** inventar endpoints fora dos `urls.py` existentes.
- **Não** tratar choices como strings na API persistida sem alinhar aos inteiros do model.
