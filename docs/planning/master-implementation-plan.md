# Plano Mestre de Implementação do Cortex

## Objetivo

Este documento organiza a implementação do Cortex em milestones coerentes com a arquitetura atual do projeto.

O plano considera:

- organização por domínio;
- módulos de domínio como agregadores estruturais;
- apps internos finos;
- regra preferencial de um app por model principal;
- arquitetura em camadas;
- evolução incremental com validação por etapas.

Este documento é o artefato macro de planejamento do projeto.  
Ele não substitui o checklist global nem os planos operacionais específicos de cada milestone, mas serve como visão principal da ordem de execução.

---

## Princípios orientadores

1. O projeto é organizado por **domínios**, não por conveniência técnica.
2. Cada domínio pode conter **um ou mais apps internos**.
3. Em regra, cada **app representa um model principal**.
4. Exceções devem ser raras e justificadas.
5. Views devem permanecer leves e delegar para as camadas apropriadas.
6. A implementação deve priorizar:
   - estrutura correta;
   - consistência do domínio;
   - integração progressiva;
   - documentação sempre atualizada.

---

## Estrutura conceitual de execução

A implementação do Cortex ocorre em três níveis:

### 1. Fundação técnica

Ajustes e consolidações da base reutilizável.

### 2. Implementação por domínio

Cada milestone trata um domínio do sistema, mas sua execução interna ocorre por apps menores.

### 3. Integração e consolidação

Etapa final de validação cruzada entre domínios, documentação e coerência estrutural.

---

# Milestone 0 — Fundação técnica

## Estado

**Concluída**

## Objetivo

Consolidar a base técnica do projeto para suportar os domínios reais do sistema.

## Foco principal

- revisão do `AppCore`
- revisão do `Auth`
- revisão do `Cortex`
- autenticação por email/CPF
- alinhamento do `AUTH_USER_MODEL`
- padronização de BasicViews
- garantia de views leves
- consolidação de convenções estruturais e de nomenclatura

## Resultado esperado

A base técnica do projeto deve estar estável, segura e coerente com a arquitetura do Cortex.

---

# Milestone 1 — Domínio Identidade

## Estado

**Concluída**

## Objetivo

Implementar o domínio `Identidade`, que fornece a base concreta de identidade do usuário no sistema.

## Estrutura do domínio

Módulo:

- `Identidade/`

Apps internos previstos:

- `usuarios/`
- `contatos/`
- `enderecos/`
- `matriculas/`

## Ordem interna recomendada

### 1.1 — `usuarios`

Responsável por:

- `Usuario`
- manager do usuário
- autenticação real do sistema
- integração com `AUTH_USER_MODEL`

### 1.2 — `contatos`

Responsável por:

- `Contato`

### 1.3 — `enderecos`

Responsável por:

- `Endereco`

### 1.4 — `matriculas`

Responsável por:

- `Matricula`

### 1.5 — integração interna do domínio

Responsável por:

- coerência entre apps do domínio
- ajustes de rotas agregadas
- validação da integração interna do módulo `Identidade`

## Resultado esperado

O projeto passa a possuir o usuário real do sistema e sua base de identidade consolidada.

---

# Milestone 2 — Domínio Organizacional

## Estado

**Concluída**

## Objetivo

Implementar o domínio `Organizacional`, responsável pela estrutura institucional e vínculos organizacionais.

## Estrutura do domínio

Módulo:

- `Organizacional/`

Apps internos previstos:

- `setores/`
- `funcoes/`
- `vinculos/`

## Ordem interna recomendada

### 2.1 — `setores`

Responsável por:

- `Setor`

### 2.2 — `funcoes`

Responsável por:

- `Funcao`
- atributo `e_gratificada`

### 2.3 — `vinculos`

Responsável por:

- `SetorVinculo`
- função obrigatória no vínculo
- monitoria como função

### 2.4 — integração interna do domínio

Responsável por:

- coerência entre `setores`, `funcoes` e `vinculos`
- validação estrutural do domínio organizacional
- preparação para integração com `PessoasInstitucionais`

## Observação importante

A validação completa da regra **“responsável do setor deve ser servidor”** depende do domínio `PessoasInstitucionais` e deve ser consolidada posteriormente.

## Resultado esperado

O projeto passa a representar estrutura institucional, funções e vínculos organizacionais de forma consistente.

---

# Milestone 3 — Domínio PessoasInstitucionais

## Estado

**Concluída**

## Objetivo

Implementar o domínio `PessoasInstitucionais`, responsável pelos perfis institucionais formais do usuário.

## Estrutura do domínio

Módulo:

- `PessoasInstitucionais/`

Apps internos sugeridos:

- `servidores/`
- `cargos/`
- `terceirizados/`
- `empresas_instituicoes/`

## Ordem interna recomendada

### 3.1 — `servidores`

Responsável por:

- `Servidor`

### 3.2 — `cargos`

Responsável por:

- `Cargo`

### 3.3 — `terceirizados`

Responsável por:

- `Terceirizado`

### 3.4 — `empresas_instituicoes`

Responsável por:

- `EmpresaInstituicao`

### 3.5 — integração interna do domínio

Responsável por:

- coerência entre os perfis institucionais
- regras de associação institucional
- consolidação da integração com `Identidade`

### 3.6 — integração com `Organizacional`

Responsável por:

- consolidar a regra de elegibilidade do responsável do setor
- validar interações entre vínculo organizacional e perfil institucional

## Resultado esperado

O projeto passa a representar formalmente servidores, terceirizados e estruturas institucionais relacionadas.

---

# Milestone 4 — Domínio Acadêmico

## Estado

**Concluída**

## Objetivo

Implementar o domínio `Academico`, responsável pelos perfis acadêmicos e vínculos com cursos.

## Estrutura do domínio

Módulo:

- `Academico/`

Apps internos sugeridos:

- `alunos/`
- `cursos/`
- `aluno_cursos/`

## Ordem interna recomendada

### 4.1 — `alunos`

Responsável por:

- `Aluno`

### 4.2 — `cursos`

Responsável por:

- `Curso`

### 4.3 — `aluno_cursos`

Responsável por:

- `AlunoCurso`

### 4.4 — integração interna do domínio

Responsável por:

- coerência entre aluno, curso e vínculo acadêmico
- alinhamento com o domínio `Identidade`

## Observação importante

Regras relacionadas à monitoria não devem ser modeladas diretamente neste domínio. Elas pertencem ao domínio `Organizacional`.

## Resultado esperado

O projeto passa a representar perfis acadêmicos e seus vínculos formais com cursos.

---

# Milestone 5 — Integração e consolidação final

## Estado

**Em andamento** — etapas 5.1–5.5 concluídas; validação funcional mínima (5.6) pendente.

## Objetivo

Consolidar a integração entre os domínios já implementados, validar invariantes cruzadas e finalizar a coerência estrutural do projeto.

## Foco principal

- integração entre `Identidade` e `PessoasInstitucionais`
- integração entre `Identidade` e `Academico`
- integração entre `Organizacional` e `PessoasInstitucionais`
- integração entre `Organizacional` e `Academico`
- revisão final das invariantes do sistema
- revisão final da documentação
- revisão final de rotas, apps, settings e convenções

## Resultado esperado

O projeto deve terminar coerente, navegável, documentado e estruturalmente consistente de ponta a ponta.

---

# Milestone Infraestrutura — Domínio Infraestrutura (v1)

## Estado

**Concluída** (v1 operacional)

## Objetivo

Implementar o domínio `Infraestrutura` para cadastro de espaço físico, recursos, autorizações e empréstimos, com permissões por função conforme ADR-002.

## Estrutura do domínio

Módulo:

- `Infraestrutura/`

Apps internos:

- `blocos/`, `salas/`, `recursos/`, `permissoes/`, `autorizacoes/`, `emprestimos/`

## Observação

Esta milestone evolui em paralelo à consolidação final (Milestone 5). O domínio está registrado em `PROJECT_APPS`, roteado em `/cortex/infraestrutura/` e documentado em `docs/planning/milestone-infraestrutura-plan.md`.

## Resultado esperado

Fluxo de liberação de recursos (chaves) substituindo o Chameco legado, com matriz L1/L2/L3 e testes das regras centrais.

---

# Ordem geral recomendada

1. Fundação técnica
2. Identidade
3. Organizacional
4. PessoasInstitucionais
5. Acadêmico
6. Integração e consolidação final

---

# Estratégia de execução dentro de cada domínio

Cada domínio deve ser executado, preferencialmente, nesta sequência:

1. estrutura física do módulo e do app
2. `models.py`
3. `business.py`, `rules.py`, `helpers.py`
4. `serializers.py`, `views.py`, `urls.py`
5. `tests.py`
6. integração interna do domínio
7. validação estrutural e documental

---

# Critérios gerais de avanço entre milestones

Uma milestone só deve ser considerada concluída quando:

1. os apps internos previstos estiverem implementados;
2. a integração interna do domínio estiver validada;
3. a documentação relevante estiver atualizada;
4. a estrutura física estiver coerente com o padrão do projeto;
5. as views estiverem aderentes ao padrão de BasicViews;
6. a lógica principal estiver nas camadas corretas;
7. os testes previstos para aquela etapa estiverem implementados e consistentes com o padrão do projeto.

---

# Artefatos complementares

Este plano mestre deve ser usado junto com:

- `docs/project/implementation-checklist.md`
- `docs/project/django-project-tree.md`
- `.github/copilot-instructions.md`
- diagramas e ADRs do projeto
- planos operacionais específicos de cada milestone, quando necessários

---

# Regras de descarte de arquivos operacionais

- Prompts operacionais podem ser descartados após implementação e validação da etapa correspondente.
- Planos de milestone podem ser descartados após o encerramento seguro da milestone, se não forem necessários como histórico.
- O checklist global, a árvore do projeto, as ADRs e as instruções do repositório devem ser preservados.

---

# Resumo executivo

O Cortex deve evoluir por milestones orientadas por domínio, mantendo a implementação real organizada em apps internos finos.

A estrutura atual recomendada é:

- `Identidade/` com apps como `usuarios`, `contatos`, `enderecos`, `matriculas`
- `Organizacional/` com apps como `setores`, `funcoes`, `vinculos`
- `PessoasInstitucionais/` com apps específicos para perfis institucionais
- `Academico/` com apps específicos para perfis acadêmicos
- `Infraestrutura/` com apps para espaço físico, recursos, autorizações e empréstimos

Esse plano substitui a visão anterior em que cada domínio era tratado como um único app principal, e passa a refletir a arquitetura atual do projeto.
