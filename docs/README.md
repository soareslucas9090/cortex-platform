# Documentação do Projeto Novo Cortex

Este diretório contém a documentação técnica, decisões arquiteturais, planejamento e diagramas do projeto.

## Estrutura da Documentação

### 📝 Decisions
Contém registros de decisões arquiteturais (ADRs - Architecture Decision Records).
- [ADR-001: Modularização por Domínio](decisions/ADR-001-modularizacao-por-dominio.md)
- [ADR-002: Permissões Cortex por Nível (L1–L3)](decisions/ADR-002-permissoes-cortex-niveis.md)

### 📊 Diagrams
Diagramas e visões gerais do sistema e produto.
- [00: README](diagrams/00-readme.md)
- [01: Product and System Overview](diagrams/01-product-and-system-overview.md)
- [02: Bounded Contexts](diagrams/02-bounded-contexts.md)
- [03: Core ERD (Entidade-Relacionamento)](diagrams/03-core-erd.md)
- [04: Aggregates and Invariants](diagrams/04-aggregates-and-invariants.md)

### 🗺️ Planning
Documentos de planejamento de implementação e marcos.
- [Master Implementation Plan](planning/master-implementation-plan.md)
- [Milestone 1: Identidade Plan](planning/milestone-1-identidade-plan.md)
- [Milestone 2: Organizacional Plan](planning/milestone-2-organizacional-plan.md)
- [Milestone 3: Pessoas Institucionais Plan](planning/milestone-3-pessoas-institucionais-plan.md)
- [Milestone 4: Acadêmico Plan](planning/milestone-4-academico-plan.md)
- [Milestone 5: Integração e Consolidação Final Plan](planning/milestone-5-integracao-e-consolidacao-final-plan.md)
- [Milestone: Importação de Usuários](planning/milestone-importacao-usuarios.md)
- [Milestone: Infraestrutura (v1)](planning/milestone-infraestrutura-plan.md)

### 🔌 API
Especificações e especificações de integração das APIs.
- [Importação de Usuários OpenAPI](api/importacao-usuarios-openapi.md)

### 📊 Schemas e Importação
Modelagens de dados, mapeamentos e regras de carga.
- [Dados Raízes da Importação](schema/dados-raizes-importacao.md)
- [Importação de Usuários](schema/importacao-usuarios.md)
- [Infraestrutura](schema/infraestrutura.md)
- [Funcionamento do Chameco legado](schema/funcionamento-antigo-sigec.md)

### 🌱 Seeds e Inicialização
Dados de sementes (seeds) e informações de carga inicial do banco.
- [Documentação DER - Cortex Seeds](seeds/documentação%20DER%20-%20cortex.md)

### 📁 Project
Documentos gerais do projeto, checklists, revisões, regras de arquitetura e guias de desenvolvimento.
- [Regras do Projeto](project/regras-do-projeto.md) — inclui contrato obrigatório de `try/except` em `business.py` (catch-all com `relancar_ou_erro_sistema`)
- [Guia: Implementação](project/guia-implementacao.md)
- [Guia: Revisão de Código](project/guia-revisao-de-codigo.md)
- [Guia: Corrigir Testes](project/guia-corrigir-testes.md)
- [AppCore Review Summary](project/appcore-review-summary.md)
- [AppCore Risks and Refactoring Priorities](project/appcore-risks-and-refactoring-priorities.md)
- [AppCore What To Keep](project/appcore-what-to-keep.md)
- [Authentication Email or CPF Design](project/authentication-email-or-cpf-design.md)
- [Django Project Tree](project/django-project-tree.md)
- [Implementation Checklist](project/implementation-checklist.md)
- [Test Users and Seed Scenarios](project/test-users-and-seed-scenarios.md)
- [Debugando com Docker](debug-docker.md)

### 📦 Domains
Diretrizes e regras específicas por domínio de negócio.
- [Identidade](domains/identidade.md)
- [Organizacional](domains/organizacional.md)
- [Pessoas Institucionais](domains/pessoas-institucionais.md)
- [Acadêmico](domains/academico.md)
