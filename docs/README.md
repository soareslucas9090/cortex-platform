# Documentação do Projeto Novo Cortex

Este diretório contém a documentação técnica, decisões arquiteturais, planejamento e diagramas do projeto.

## Estrutura da Documentação

### 📝 Decisions
Contém registros de decisões arquiteturais (ADRs - Architecture Decision Records).
- [ADR-001: Modularização por Domínio](decisions/ADR-001-modularizacao-por-dominio.md)

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

### 🔌 API
Especificações e especificações de integração das APIs.
- [Importação de Usuários OpenAPI](api/importacao-usuarios-openapi.md)

### 📊 Schemas e Importação
Modelagens de dados, mapeamentos e regras de carga.
- [Dados Raízes da Importação](schema/dados-raizes-importacao.md)
- [Importação de Usuários](schema/importacao-usuarios.md)

### 🌱 Seeds e Inicialização
Dados de sementes (seeds) e informações de carga inicial do banco.
- [Documentação DER - Cortex Seeds](seeds/documentação%20DER%20-%20cortex.md)

### 📁 Project
Documentos gerais do projeto, checklists, revisões e estratégias de refatoração.
- [AppCore Review Summary](project/appcore-review-summary.md)
- [AppCore Risks and Refactoring Priorities](project/appcore-risks-and-refactoring-priorities.md)
- [AppCore What To Keep](project/appcore-what-to-keep.md)
- [Authentication Email or CPF Design](project/authentication-email-or-cpf-design.md)
- [Django Project Tree](project/django-project-tree.md)
- [Implementation Checklist](project/implementation-checklist.md)
- [Test Users and Seed Scenarios](project/test-users-and-seed-scenarios.md)

### 🤖 Antigravity & AI Agents
Instruções, regras arquiteturais e skills para uso com agentes de inteligência artificial (como o Antigravity).
- [Regras do Projeto](antigravity/project-rules.md)
- [Skill: Implementação](antigravity/skill-implementation.md)
- [Skill: Revisão de Código](antigravity/skill-code-review.md)
- [Skill: Corrigir Testes](antigravity/skill-test-fixing.md)

#### Diretrizes por Domínio:
- [Domínio: Identidade](antigravity/rules/identidade.md)
- [Domínio: Organizacional](antigravity/rules/organizacional.md)
- [Domínio: Pessoas Institucionais](antigravity/rules/pessoas-institucionais.md)
- [Domínio: Acadêmico](antigravity/rules/academico.md)
