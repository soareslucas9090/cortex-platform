# Diretrizes do Domínio: Organizacional

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Organizacional** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Organizacional` gerencia a estrutura administrativa da instituição: **setores**, **funções** (papéis desempenhados no setor, incluindo monitoria acadêmica) e **vínculos** que associam usuários a setores.

Um **mesmo usuário** pode ter **vários vínculos** (N setores, papéis distintos). O papel no setor é sempre a FK **`Funcao`** no vínculo — **não** use flags booleanas de “monitor” ou “chefe” no `Usuario` ou no `Setor`.

Seeds de referência: [documentação DER - cortex](../seeds/documentação%20DER%20-%20cortex.md).

### Modelos e Relacionamentos

- **Setor**: `nome`, `sigla` (única), `ativo`.
- **Funcao**: catálogo de papéis (`papel_funcao` único), com metadados de negócio (abaixo).
- **SetorVinculo**: `usuario` + `setor` + `funcao` (opcional no model, mas exigida nas regras de criação) + `responsavel`.

### Estrutura de Apps

```text
Organizacional/
├── __init__.py
├── urls.py
├── setores/         # App Django do model Setor
├── funcoes/         # App Django do model Funcao
└── vinculos/        # App Django do model SetorVinculo
```

---

## Prefixo HTTP

**`/cortex/organizacional/`**

---

## Model `Funcao` (campos reais)

Além de `papel_funcao`, `descricao` e `ativo`:

| Campo | Tipo | Significado |
| ----- | ---- | ----------- |
| `categoria` | `CharField` | `CategoriaFuncao`: `diretor`, `coordenador`, `chefe` (default `coordenador`) |
| `e_gratificada` | `BooleanField` | Indica função gratificada |
| `exige_aluno` | `BooleanField` | Se `True`, só **aluno ativo** pode ocupar o vínculo com essa função |

**Monitoria** (e papéis exclusivos de discente) modelam-se como **`Funcao`** com `exige_aluno=True`, validado em `SetorVinculoRules.usuario_e_aluno_se_exigido` — não no domínio Acadêmico.

Permissões de outros módulos (Infraestrutura, Transporte) ligam-se a `Funcao` via tabelas dedicadas (`PermissaoFuncaoInfraestrutura`, `PermissaoFuncaoTransporte`), **sem** campos extras em `Funcao`.

---

## Regras de `SetorVinculo`

### Responsável principal do setor

- Campo **`responsavel`** (`BooleanField`): indica responsável principal daquele vínculo.
- Apenas **servidor ativo** pode ser marcado responsável (`SetorVinculoRules.usuario_e_servidor`).
- O setor deve manter **ao menos um** vínculo com `responsavel=True` (`setor_mantem_responsavel` ao encerrar ou remover flag).
- Definir/remover responsável: endpoints administrativos `definir-responsavel` / `remover-responsavel` (L3).

### Função no vínculo

- Unicidade lógica: mesma combinação `usuario` + `setor` + `funcao` não pode repetir (`vinculo_sem_duplicata`).
- Função e setor devem estar **ativos** na criação.
- Atualização de função: `PATCH .../vinculos/{pk}/funcao/`.

#### Modelagem de referência

```python
class SetorVinculo(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, ...)
    setor = models.ForeignKey('setores.Setor', on_delete=models.PROTECT, ...)
    funcao = models.ForeignKey('funcoes.Funcao', on_delete=models.PROTECT, null=True, blank=True, ...)
    responsavel = models.BooleanField('Responsável', default=False)
```

---

## Permissões HTTP (ADR-002)

Padrão Cortex; detalhes completos da matriz em [ADR-002](../decisions/ADR-002-permissoes-cortex-niveis.md) e [regras-do-projeto](../project/regras-do-projeto.md).

| Recurso | Leitura | Escrita |
| ------- | ------- | ------- |
| **Setores**, **Funções** (catálogos) | Autenticado (`IsAuthenticatedMixin`) — lista completa | L3 (`IsAdminMixin`) |
| **Vínculos do setor** | Autenticado com escopo (`IsOwnerOrAdminMixin` + `escopar_queryset_cortex`): L2+ vê todos do setor; L1 só os próprios | L3 |

Query params de listagem **apenas estreitam** o resultado; nunca expandem o escopo de permissão.

---

## Endpoints principais

Paths relativos a `/cortex/organizacional/`.

### Setores

| Método | Path |
| ------ | ---- |
| GET, POST | `setores/` |
| GET, PATCH | `setores/{pk}/` |
| POST | `setores/{pk}/desativar/`, `setores/{pk}/reativar/` |

### Funções

| Método | Path |
| ------ | ---- |
| GET, POST | `funcoes/` |
| GET, PATCH | `funcoes/{pk}/` |
| POST | `funcoes/{pk}/desativar/`, `funcoes/{pk}/reativar/` |

### Vínculos (por setor)

| Método | Path |
| ------ | ---- |
| GET, POST | `setores/{setor_pk}/vinculos/` |
| POST | `setores/{setor_pk}/vinculos/{pk}/encerrar/` |
| POST | `setores/{setor_pk}/vinculos/{pk}/definir-responsavel/` |
| POST | `setores/{setor_pk}/vinculos/{pk}/remover-responsavel/` |
| PATCH | `setores/{setor_pk}/vinculos/{pk}/funcao/` |

Filtros de listagem de vínculos (entre outros): `nome_usuario`, `cpf_usuario`, `papel_funcao`, `responsavel`, `paginacao`.

---

## O que NÃO fazer

- **Não** modelar monitoria ou cargo de confiança como campo solto em `Usuario` / `Aluno`.
- **Não** inventar rotas fora de `Organizacional/*/urls.py`.
- **Não** duplicar aqui o contrato global de `try/except` em business, mixins AppCore ou política de testes — use os guias em `docs/project/`.
- **Não** desativar `Funcao` em uso em vínculos (`FuncaoRules.pode_desativar`).
