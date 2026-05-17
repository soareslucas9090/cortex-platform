# Checklist de Implementação do Cortex

## Objetivo

Este documento organiza a implementação inicial do Cortex em etapas práticas, coerentes com:

- a modularização por domínio;
- o ERD central;
- os agregados e invariantes já definidos;
- a arquitetura em camadas da base Django/DRF.

O objetivo é permitir uma execução incremental, previsível e consistente, evitando pular etapas estruturais importantes.

---

## Princípios desta checklist

1. Implementar primeiro o que serve de base para os demais domínios.
2. Criar estrutura mínima por domínio antes de expandir features.
3. Consolidar models e regras críticas antes de avançar para endpoints mais completos.
4. Evitar colocar regra de negócio diretamente em views.
5. Priorizar consistência do domínio antes de refino de interface ou otimizações.

---

# Fase 0 — Preparação da base

## Estrutura e documentação

- [ ] Garantir existência da pasta `docs/`
- [ ] Criar `docs/diagrams/02-bounded-contexts.md`
- [ ] Criar `docs/decisions/ADR-001-modularizacao-por-dominio.md`
- [ ] Criar `docs/project/django-project-tree.md`
- [ ] Criar `docs/diagrams/03-core-erd.md`
- [ ] Criar `docs/diagrams/04-aggregates-and-invariants.md`

## Revisão da base técnica

- [ ] Revisar `Cortex/settings.py`
- [ ] Confirmar estratégia de `AUTH_USER_MODEL`
- [ ] Confirmar que o login será por `cpf`
- [ ] Revisar `AppCore` para garantir aderência ao novo domínio
- [ ] Validar se a estrutura atual de autenticação está pronta para o model real de usuário
- [ ] Revisar convenções de nomenclatura em português
- [ ] Revisar se os apps novos entrarão em `PROJECT_APPS`

## Decisão de implementação

- [ ] Confirmar ordem de criação dos apps:
  - [ ] `identidade`
  - [ ] `organizacional`
  - [ ] `pessoas_institucionais`
  - [ ] `academico`

---

# Fase 1 — Criação física dos apps de domínio

## App `identidade`

- [ ] Criar diretório `identidade/`
- [ ] Criar `identidade/__init__.py`
- [ ] Criar `identidade/apps.py`
- [ ] Criar `identidade/models.py`
- [ ] Criar `identidade/business.py`
- [ ] Criar `identidade/rules.py`
- [ ] Criar `identidade/helpers.py`
- [ ] Criar `identidade/serializers.py`
- [ ] Criar `identidade/views.py`
- [ ] Criar `identidade/urls.py`

## App `organizacional`

- [ ] Criar diretório `organizacional/`
- [ ] Criar `organizacional/__init__.py`
- [ ] Criar `organizacional/apps.py`
- [ ] Criar `organizacional/models.py`
- [ ] Criar `organizacional/business.py`
- [ ] Criar `organizacional/rules.py`
- [ ] Criar `organizacional/helpers.py`
- [ ] Criar `organizacional/serializers.py`
- [ ] Criar `organizacional/views.py`
- [ ] Criar `organizacional/urls.py`
- [ ] Criar `organizacional/choices.py` se necessário

## App `pessoas_institucionais`

- [ ] Criar diretório `pessoas_institucionais/`
- [ ] Criar `pessoas_institucionais/__init__.py`
- [ ] Criar `pessoas_institucionais/apps.py`
- [ ] Criar `pessoas_institucionais/models.py`
- [ ] Criar `pessoas_institucionais/business.py`
- [ ] Criar `pessoas_institucionais/rules.py`
- [ ] Criar `pessoas_institucionais/helpers.py`
- [ ] Criar `pessoas_institucionais/serializers.py`
- [ ] Criar `pessoas_institucionais/views.py`
- [ ] Criar `pessoas_institucionais/urls.py`
- [ ] Criar `pessoas_institucionais/choices.py` se necessário

## App `academico`

- [ ] Criar diretório `academico/`
- [ ] Criar `academico/__init__.py`
- [ ] Criar `academico/apps.py`
- [ ] Criar `academico/models.py`
- [ ] Criar `academico/business.py`
- [ ] Criar `academico/rules.py`
- [ ] Criar `academico/helpers.py`
- [ ] Criar `academico/serializers.py`
- [ ] Criar `academico/views.py`
- [ ] Criar `academico/urls.py`
- [ ] Criar `academico/choices.py` se necessário

---

# Fase 2 — Configuração do projeto para reconhecer os domínios

## `settings.py`

- [ ] Adicionar `identidade` em `PROJECT_APPS`
- [ ] Adicionar `organizacional` em `PROJECT_APPS`
- [ ] Adicionar `pessoas_institucionais` em `PROJECT_APPS`
- [ ] Adicionar `academico` em `PROJECT_APPS`

## `urls.py`

- [ ] Incluir rotas de `identidade`
- [ ] Incluir rotas de `organizacional`
- [ ] Incluir rotas de `pessoas_institucionais`
- [ ] Incluir rotas de `academico`

## App de autenticação

- [ ] Ajustar serializers de login para refletir login por CPF
- [ ] Ajustar documentação Swagger do login
- [ ] Validar integração com o `Usuario` real do domínio `identidade`

---

# Fase 3 — Implementação do domínio Identidade

## Models

- [ ] Implementar `Usuario`
- [ ] Implementar manager de usuário
- [ ] Definir `USERNAME_FIELD = 'cpf'`
- [ ] Implementar `Contato`
- [ ] Implementar `Endereco`
- [ ] Implementar `Matricula`

## Regras de modelagem

- [ ] Garantir unicidade de `cpf`
- [ ] Garantir relação correta entre `Usuario` e seus dados auxiliares
- [ ] Decidir cardinalidade final de `Contato`
- [ ] Decidir se `Endereco` será estritamente 1:1

## Business / Rules / Helpers

- [ ] Criar regras de criação de usuário
- [ ] Criar regras de atualização cadastral
- [ ] Criar helpers de consulta por CPF
- [ ] Criar regras para contatos, endereço e matrícula

## Serializers / Views

- [ ] Criar serializer de criação de usuário
- [ ] Criar serializer de atualização
- [ ] Criar serializers de resposta
- [ ] Criar endpoints básicos de consulta e manutenção
- [ ] Documentar endpoints com `drf-spectacular`

## Migrations

- [ ] Gerar migrations de `identidade`
- [ ] Revisar migrations antes de aplicar
- [ ] Aplicar migrations

---

# Fase 4 — Implementação do domínio Organizacional

## Models

- [ ] Implementar `Setor`
- [ ] Implementar `Funcao`
- [ ] Adicionar `e_gratificada` em `Funcao`
- [ ] Implementar `SetorVinculo`

## Regras de modelagem

- [ ] Garantir função obrigatória em `SetorVinculo`
- [ ] Garantir relação entre `Setor`, `Usuario` e `Funcao`
- [ ] Remover qualquer ideia de `monitor` como booleano
- [ ] Representar monitoria como `Funcao`

## Regras de negócio

- [ ] Garantir que setor tenha responsável
- [ ] Garantir que responsável seja servidor
- [ ] Garantir que troca de responsável não deixe setor inconsistente
- [ ] Garantir que usuário possa possuir múltiplos vínculos setoriais

## Business / Rules / Helpers

- [ ] Criar regras para criação de setor
- [ ] Criar regras para criação de vínculo
- [ ] Criar regras para definição de responsável
- [ ] Criar helpers de consulta de vínculos por setor
- [ ] Criar helpers de consulta de vínculos por usuário

## Serializers / Views

- [ ] Criar serializers de setor
- [ ] Criar serializers de função
- [ ] Criar serializers de vínculo
- [ ] Criar endpoints de cadastro e listagem
- [ ] Criar endpoint para atribuição/troca de responsável
- [ ] Documentar tudo com Swagger

## Migrations

- [ ] Gerar migrations de `organizacional`
- [ ] Revisar migrations
- [ ] Aplicar migrations

---

# Fase 5 — Implementação do domínio PessoasInstitucionais

## Models

- [ ] Implementar `Cargo`
- [ ] Implementar `Servidor`
- [ ] Implementar `EmpresaInstituicao`
- [ ] Implementar `Terceirizado`

## Regras de modelagem

- [ ] Garantir que `Cargo` seja exclusivo de `Servidor`
- [ ] Garantir vínculo 1:1 entre `Usuario` e `Servidor`
- [ ] Garantir vínculo 1:1 entre `Usuario` e `Terceirizado`
- [ ] Garantir associação entre `Terceirizado` e `EmpresaInstituicao`

## Regras de negócio

- [ ] Validar elegibilidade de servidor para responsabilidade de setor
- [ ] Validar criação consistente de terceirizado com empresa
- [ ] Definir se usuário pode acumular perfis diferentes no sistema

## Business / Rules / Helpers

- [ ] Criar regras de criação de servidor
- [ ] Criar regras de criação de terceirizado
- [ ] Criar helpers de consulta por cargo
- [ ] Criar helpers de consulta por empresa

## Serializers / Views

- [ ] Criar serializers de cargo
- [ ] Criar serializers de servidor
- [ ] Criar serializers de empresa
- [ ] Criar serializers de terceirizado
- [ ] Criar endpoints básicos
- [ ] Documentar endpoints com Swagger

## Migrations

- [ ] Gerar migrations de `pessoas_institucionais`
- [ ] Revisar migrations
- [ ] Aplicar migrations

---

# Fase 6 — Implementação do domínio Academico

## Models

- [ ] Implementar `Aluno`
- [ ] Implementar `Curso`
- [ ] Implementar `AlunoCurso`

## Regras de modelagem

- [ ] Garantir vínculo 1:1 entre `Usuario` e `Aluno`
- [ ] Garantir vínculo entre `Aluno` e `Curso` por `AlunoCurso`
- [ ] Evitar modelar monitoria diretamente em `Aluno`

## Regras de negócio

- [ ] Validar criação de aluno a partir de usuário existente
- [ ] Validar vínculos acadêmicos
- [ ] Preservar histórico acadêmico por meio de `AlunoCurso`

## Business / Rules / Helpers

- [ ] Criar regras de criação de aluno
- [ ] Criar regras de criação de curso
- [ ] Criar regras de vínculo aluno-curso
- [ ] Criar helpers de consulta de cursos por aluno
- [ ] Criar helpers de consulta de alunos por curso

## Serializers / Views

- [ ] Criar serializers de aluno
- [ ] Criar serializers de curso
- [ ] Criar serializers de vínculo acadêmico
- [ ] Criar endpoints básicos
- [ ] Documentar endpoints com Swagger

## Migrations

- [ ] Gerar migrations de `academico`
- [ ] Revisar migrations
- [ ] Aplicar migrations

---

# Fase 7 — Integração entre domínios

## Integração organizacional + perfis

- [ ] Validar regra de responsável de setor usando perfil `Servidor`
- [ ] Validar monitoria com base em `SetorVinculo + Funcao`

## Integração identidade + autenticação

- [ ] Garantir login por CPF
- [ ] Garantir compatibilidade do serializer de login com `Usuario`

## Integração acadêmica + organizacional

- [ ] Garantir que aluno monitor seja tratado no domínio correto
- [ ] Evitar duplicação de regras de monitoria

---

# Fase 8 — Refinamento documental

## Atualizações obrigatórias

- [ ] Atualizar `docs/diagrams/03-core-erd.md` caso a modelagem mude
- [ ] Atualizar `docs/diagrams/04-aggregates-and-invariants.md` caso as invariantes mudem
- [ ] Atualizar `docs/decisions/ADR-001-modularizacao-por-dominio.md` se houver mudança arquitetural relevante
- [ ] Atualizar `.github/copilot-instructions.md` quando houver mudança significativa na estrutura do projeto

---

# Fase 9 — Validação funcional mínima

## Cenários mínimos

- [ ] Criar usuário com CPF
- [ ] Criar servidor com cargo
- [ ] Criar setor
- [ ] Criar função
- [ ] Vincular servidor a setor com função
- [ ] Definir responsável de setor
- [ ] Criar aluno
- [ ] Vincular aluno a curso
- [ ] Vincular aluno monitor a setor com função `monitor`
- [ ] Criar terceirizado com empresa

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

A implementação do Cortex deve seguir uma ordem orientada por domínio:

1. `identidade`
2. `organizacional`
3. `pessoas_institucionais`
4. `academico`

Esse checklist transforma a visão arquitetural já definida em uma sequência prática de execução, reduzindo risco de retrabalho e ajudando a preservar a consistência do domínio desde o início.
