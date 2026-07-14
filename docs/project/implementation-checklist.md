# Checklist de Implementação do Cortex

## Objetivo

Este documento organiza a implementação inicial do Cortex em etapas práticas, coerentes com:

- a modularização por domínio com apps internos;
- o ERD central;
- os agregados e invariantes já definidos;
- a arquitetura em camadas da base Django/DRF.

O objetivo é permitir uma execução incremental, previsível e consistente, evitando pular etapas estruturais importantes.

---

## Princípios desta checklist

1. Implementar primeiro o que serve de base para os demais domínios.
2. Criar estrutura mínima por domínio antes de expandir features.
3. Domínio é módulo agregador — apps internos representam models principais.
4. Consolidar models e regras críticas antes de avançar para endpoints mais completos.
5. Evitar colocar regra de negócio diretamente em views.
6. Priorizar consistência do domínio antes de refino de interface ou otimizações.
7. Testes fazem parte da implementação — cada app deve ter testes antes de avançar à próxima milestone.

---

# Fase 0 — Preparação da base

## Estrutura e documentação

- [x] Garantir existência da pasta `docs/`
- [x] Criar `docs/diagrams/02-bounded-contexts.md`
- [x] Criar `docs/decisions/ADR-001-modularizacao-por-dominio.md`
- [x] Criar `docs/project/django-project-tree.md`
- [x] Criar `docs/diagrams/03-core-erd.md`
- [x] Criar `docs/diagrams/04-aggregates-and-invariants.md`

## Revisão da base técnica

- [x] Revisar `Cortex/settings.py`
- [x] Confirmar estratégia de `AUTH_USER_MODEL`
- [x] Confirmar que o login será por `cpf`
- [x] Revisar `AppCore` para garantir aderência ao novo domínio
- [x] Validar que a estrutura de autenticação está pronta para o model real de usuário
- [x] Revisar convenções de nomenclatura em português
- [x] Registrar apps internos em `PROJECT_APPS` no formato `Modulo.app`

## Decisão de implementação

- [x] Confirmar ordem de criação dos módulos de domínio:
  - [x] `Identidade/` (Milestone 1)
  - [x] `Organizacional/` (Milestone 2)
  - [x] `PessoasInstitucionais/` (Milestone 3)
  - [x] `Academico/` (Milestone 4)

---

# Milestone 1 — Domínio Identidade

## Estrutura do módulo

- [x] Criar diretório `Identidade/`
- [x] Criar `Identidade/__init__.py`
- [x] Criar `Identidade/urls.py` (agregador do módulo, com `app_name = 'identidade'`)
- [x] Registrar módulo em `Cortex/urls.py`: `path('identidade/', include('Identidade.urls'))`

## App `Identidade/usuarios/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Identidade.usuarios'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Usuario` com `USERNAME_FIELD = 'cpf'`
- [x] Implementar `business.py`, `rules.py`, `helpers.py`
- [x] Implementar `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Identidade/urls.py`
- [x] Implementar testes em `tests/`

## App `Identidade/contatos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Identidade.contatos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Contato`
- [x] Implementar `business.py`, `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Identidade/urls.py`
- [x] Implementar testes em `tests/`

## App `Identidade/enderecos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Identidade.enderecos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Endereco`
- [x] Implementar `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Identidade/urls.py`
- [x] Implementar testes em `tests/`

## App `Identidade/matriculas/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Identidade.matriculas'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Matricula`
- [x] Implementar `business.py`, `rules.py`, `choices.py`, `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Identidade/urls.py`
- [x] Implementar testes em `tests/`

## Integração interna do domínio Identidade

- [x] Validar coerência entre os 4 apps do módulo
- [x] Validar roteamento agregado em `Identidade/urls.py`
- [x] Garantir login por CPF integrado com `Auth`
- [x] Revisar testes de integração entre apps do domínio

---

# Milestone 2 — Domínio Organizacional

## Estrutura do módulo

- [x] Criar diretório `Organizacional/`
- [x] Criar `Organizacional/__init__.py`
- [x] Criar `Organizacional/urls.py` (agregador do módulo, com `app_name = 'organizacional'`)
- [x] Registrar módulo em `Cortex/urls.py`: `path('organizacional/', include('Organizacional.urls'))`

## App `Organizacional/setores/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Organizacional.setores'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Setor`
- [x] Implementar `business.py`, `rules.py`, `helpers.py`, `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Organizacional/urls.py`
- [x] Implementar testes em `tests/`

## App `Organizacional/funcoes/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Organizacional.funcoes'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Funcao` com atributo `e_gratificada`
- [x] Implementar `business.py`, `rules.py`, `helpers.py`, `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Organizacional/urls.py`
- [x] Implementar testes em `tests/`

## App `Organizacional/vinculos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Organizacional.vinculos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `SetorVinculo` com FK para `Funcao` (monitoria via Funcao, não booleano)
- [x] Implementar `business.py`, `rules.py`, `helpers.py`, `serializers.py`, `views.py`, `urls.py`
- [x] Incluir rotas no `Organizacional/urls.py`
- [x] Implementar testes em `tests/`

## Integração interna do domínio Organizacional

- [x] Validar coerência entre `setores`, `funcoes` e `vinculos`
- [x] Garantir que regras de responsável de setor estejam implementadas
- [x] Revisar testes de integração entre apps do domínio
- [x] Preparar integração futura com `PessoasInstitucionais` (regra de elegibilidade de responsável)

---

# Milestone 3 — Domínio PessoasInstitucionais

## Estrutura do módulo

- [x] Criar diretório `PessoasInstitucionais/`
- [x] Criar `PessoasInstitucionais/__init__.py`
- [x] Criar `PessoasInstitucionais/urls.py` (agregador do módulo, com `app_name = 'pessoas-institucionais'`)
- [x] Registrar módulo em `Cortex/urls.py`

## App `PessoasInstitucionais/cargos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'PessoasInstitucionais.cargos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Cargo`
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `PessoasInstitucionais/urls.py`
- [x] Implementar testes em `tests/`

## App `PessoasInstitucionais/servidores/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'PessoasInstitucionais.servidores'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Servidor` (OneToOne com `Usuario`)
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `PessoasInstitucionais/urls.py`
- [x] Implementar testes em `tests/`

## App `PessoasInstitucionais/empresas_instituicoes/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'PessoasInstitucionais.empresas_instituicoes'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `EmpresaInstituicao`
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `PessoasInstitucionais/urls.py`
- [x] Implementar testes em `tests/`

## App `PessoasInstitucionais/terceirizados/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'PessoasInstitucionais.terceirizados'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Terceirizado` (OneToOne com `Usuario`)
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `PessoasInstitucionais/urls.py`
- [x] Implementar testes em `tests/`

## Integração interna do domínio PessoasInstitucionais

- [x] Validar coerência entre os apps do módulo
- [x] Consolidar regra de elegibilidade do responsável de setor (integração com `Organizacional`)
- [x] Revisar testes de integração

---

# Milestone 4 — Domínio Acadêmico

## Estrutura do módulo

- [x] Criar diretório `Academico/`
- [x] Criar `Academico/__init__.py`
- [x] Criar `Academico/urls.py` (agregador do módulo, com `app_name = 'academico'`)
- [x] Registrar módulo em `Cortex/urls.py`

## App `Academico/alunos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Academico.alunos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Aluno` (OneToOne com `Usuario`)
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `Academico/urls.py`
- [x] Implementar testes em `tests/`

## App `Academico/cursos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Academico.cursos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `Curso`
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `Academico/urls.py`
- [x] Implementar testes em `tests/`

## App `Academico/aluno_cursos/`

- [x] Criar estrutura física do app
- [x] Criar `apps.py` com `name = 'Academico.aluno_cursos'`
- [x] Registrar em `PROJECT_APPS`
- [x] Implementar `models.py` — model `AlunoCurso`
- [x] Implementar camadas e endpoints
- [x] Incluir rotas no `Academico/urls.py`
- [x] Implementar testes em `tests/`

## Integração interna do domínio Acadêmico

- [x] Validar coerência entre os apps do módulo
- [x] Garantir alinhamento com `Identidade` (aluno deriva de Usuario)
- [x] Revisar testes de integração

---

# Milestone 5 — Integração e consolidação final

## Integração entre domínios

- [x] Validar regra de responsável de setor usando perfil `Servidor`
- [x] Validar monitoria com base em `SetorVinculo + Funcao`
- [x] Garantir login por CPF integrado com `Usuario`
- [x] Garantir que aluno monitor seja tratado no domínio correto
- [x] Evitar duplicação de regras de monitoria entre domínios

## Refinamento documental

- [x] Atualizar `docs/diagrams/03-core-erd.md` caso a modelagem tenha mudado
- [x] Atualizar `docs/diagrams/04-aggregates-and-invariants.md` caso as invariantes tenham mudado
- [x] Atualizar `docs/decisions/ADR-001-modularizacao-por-dominio.md` se houver mudança arquitetural relevante
- [x] Atualizar `.github/copilot-instructions.md` quando houver mudança significativa na estrutura do projeto

## Revisão estrutural e documental (etapa 5.5)

- [x] Revisar `Cortex/settings.py` e apps em `PROJECT_APPS`
- [x] Revisar `Cortex/urls.py` e rotas agregadas por domínio
- [x] Revisar `urls.py` agregadores de cada módulo de domínio
- [x] Atualizar `docs/project/django-project-tree.md`
- [x] Atualizar `README.md` na raiz do repositório
- [x] Atualizar `.github/copilot-instructions.md`
- [x] Alinhar checklist global e plano mestre com a estrutura real

## Validação funcional mínima

- [x] Criar usuário com CPF
- [x] Criar servidor com cargo
- [x] Criar setor
- [x] Criar função
- [x] Vincular servidor a setor com função
- [x] Definir responsável de setor
- [x] Criar aluno
- [x] Vincular aluno a curso
- [x] Vincular aluno monitor a setor com função `monitor`
- [x] Criar terceirizado com empresa

---

# Itens para decisão antes de aprofundar implementação

- [ ] Cardinalidade final de `Contato`
- [ ] Cardinalidade exata de `Matricula`
- [ ] Regras de coexistência de perfis no mesmo usuário
- [ ] Necessidade de datas de início/fim em `SetorVinculo`
- [ ] Necessidade de histórico de mudança de função
- [ ] Lista inicial oficial de funções
- [ ] Lista inicial oficial de cargos
- [ ] Lista inicial oficial de setores
- [ ] Necessidade de choices para categoria de servidor
- [ ] Estratégia de seed inicial

---

# Resumo executivo

A implementação do Cortex segue uma ordem orientada por domínio, com cada domínio organizado como módulo agregador contendo apps internos finos:

| Milestone | Módulo de domínio        | Apps internos                                                    | Status       |
| --------- | ------------------------ | ---------------------------------------------------------------- | ------------ |
| 1         | `Identidade/`            | `usuarios`, `contatos`, `enderecos`, `matriculas`                | Concluído    |
| 2         | `Organizacional/`        | `setores`, `funcoes`, `vinculos`                                 | Concluído    |
| 3         | `PessoasInstitucionais/` | `cargos`, `servidores`, `empresas_instituicoes`, `terceirizados` | Concluído    |
| 4         | `Academico/`             | `alunos`, `cursos`, `aluno_cursos`                               | Concluído    |
| 5         | —                        | Integração, consolidação e validação final                       | Em andamento |
| Infra     | `Infraestrutura/`        | `blocos`, `salas`, `recursos`, `permissoes`, `autorizacoes`, `emprestimos` | v1 concluída |

Esse checklist transforma a visão arquitetural já definida em uma sequência prática de execução, reduzindo risco de retrabalho e ajudando a preservar a consistência do domínio desde o início.
