# Diretrizes do Domínio: Pessoas Institucionais

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Pessoas Institucionais** do projeto Cortex.

## Visão Geral do Domínio

O domínio `PessoasInstitucionais` gerencia colaboradores institucionais (**servidores** e **terceirizados**), além dos catálogos **cargo** e **empresa/instituição**.

### Modelos e Relacionamentos

- **Cargo**: cargos públicos ou posições estruturadas. Seeds: [documentação DER - cortex](../seeds/documentação%20DER%20-%20cortex.md).
- **Servidor**: herança 1:1 com `Usuario`; **cargo obrigatório**; categoria docente ou técnico-administrativo; **matrícula opcional** com unicidade global quando preenchida.
- **EmpresaInstituicao**: empresas parceiras. Seeds no mesmo DER.
- **Terceirizado**: herança 1:1 com `Usuario`; **empresa obrigatória**; **cargo opcional**; datas de vínculo; matrícula opcional única global.
- **Estagiario**: **não implementado** — apenas planejado na hierarquia de produto. **Não** criar app, model ou endpoints de estagiário sem marco explícito; agentes não devem implementar sozinhos.

### Estrutura de Apps

```text
PessoasInstitucionais/
├── __init__.py
├── urls.py
├── cargos/                  # Cargo
├── servidores/              # Servidor
├── empresas_instituicoes/   # EmpresaInstituicao
└── terceirizados/           # Terceirizado
```

(Não existe app `estagiarios/`.)

---

## Prefixo HTTP

**`/cortex/pessoas-institucionais/`**

---

## Regras Específicas do Domínio

### Herança com `Usuario`

**OneToOneField com `primary_key=True`** (herança física), evitando multi-table inheritance nativa do Django.

### Servidor

| Campo | Regra |
| ----- | ----- |
| `cargo` | FK **obrigatória** (`PROTECT`) |
| `categoria` | `IntegerChoices`: `DOCENTE = 1`, `TECNICO_ADMINISTRATIVO = 2` |
| `matricula` | Opcional; constraint de **unicidade global** quando não nula |
| `ativo` | Default `True` |

Não há campo de jornada de trabalho no model atual — **não documentar nem inventar** horas semanais/dedicção exclusiva neste domínio.

### Terceirizado

| Campo | Regra |
| ----- | ----- |
| `empresa_instituicao` | FK **obrigatória** |
| `cargo` | FK **opcional** (`SET_NULL`) |
| `data_inicio`, `data_fim` | Opcionais; `data_fim` nula = vínculo em aberto |
| `matricula` | Opcional; unicidade global quando preenchida |
| `ativo` | Default `True` |

Matrícula em servidores/terceirizados e em `AlunoCurso` alimenta login por matrícula em Identidade (ver [identidade.md](identidade.md)).

---

## Permissões HTTP (ADR-002)

| Recurso | Leitura | Escrita |
| ------- | ------- | ------- |
| **Cargos** | Autenticado (catálogo) | L3 |
| **Empresas** | Autenticado (catálogo); L1 recebe lista vazia na matriz de escopo de negócio onde aplicável | L3 |
| **Servidores**, **Terceirizados** | `IsOwnerOrAdminMixin`: L2+ todos; L1 só o próprio | L3 |

---

## Endpoints principais

Paths relativos a `/cortex/pessoas-institucionais/`.

### Cargos

| Método | Path |
| ------ | ---- |
| GET, POST | `cargos/` |
| GET, PATCH | `cargos/{pk}/` |
| POST | `cargos/{pk}/desativar/`, `cargos/{pk}/reativar/` |

### Empresas

| Método | Path |
| ------ | ---- |
| GET, POST | `empresas/` |
| GET, PATCH | `empresas/{pk}/` |
| POST | `empresas/{pk}/desativar/`, `empresas/{pk}/reativar/` |

### Servidores

| Método | Path |
| ------ | ---- |
| GET, POST | `servidores/` |
| GET, PATCH | `servidores/{pk}/` |
| POST | `servidores/{pk}/desativar/`, `servidores/{pk}/reativar/` |

(`pk` do servidor = `usuario_id`.)

### Terceirizados

| Método | Path |
| ------ | ---- |
| GET, POST | `terceirizados/` |
| GET, PATCH | `terceirizados/{pk}/` |
| POST | `terceirizados/{pk}/desativar/`, `terceirizados/{pk}/reativar/` |

---

## O que NÃO fazer

- **Não** implementar **Estagiario** sem demanda de produto e app dedicado.
- **Não** adicionar jornada de trabalho ou campos legados ausentes do `Servidor` atual.
- **Não** inventar paths fora dos `urls.py` das apps.
- **Não** duplicar regras de matrícula/CPF — delegar a Identidade.
