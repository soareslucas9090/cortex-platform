# Plano da Milestone 3 — Domínio PessoasInstitucionais

## Objetivo

A Milestone 3 existe para implementar o domínio `PessoasInstitucionais` do Cortex.

Esse domínio deve representar os perfis institucionais formais associados ao usuário do sistema, consolidando a modelagem de vínculos institucionais e preparando o terreno para regras interdomínio que dependem dessa formalização.

Ao final desta milestone, o projeto deve possuir uma implementação coerente para:

- `Cargo`
- `EmpresaInstituicao`
- `Servidor`
- `Terceirizado`

---

## Resultado esperado ao final da milestone

Ao final da Milestone 3, o sistema deve estar apto a:

1. cadastrar e manter cargos institucionais;
2. cadastrar e manter empresas ou instituições associadas a vínculos externos;
3. representar usuários que sejam servidores;
4. representar usuários que sejam terceirizados;
5. consolidar a base institucional necessária para validar regras organizacionais dependentes de perfil formal;
6. preparar o sistema para integração posterior com o domínio acadêmico.

---

## Estrutura do domínio

### Módulo de domínio
- `PessoasInstitucionais/`

### Apps internos previstos
- `cargos/`
- `empresas_instituicoes/`
- `servidores/`
- `terceirizados/`

---

## Escopo da milestone

## 1. Models do domínio

Esta milestone deve incluir os seguintes models principais:

- `Cargo`
- `EmpresaInstituicao`
- `Servidor`
- `Terceirizado`

### Papel de cada model

#### `Cargo`
Representa o cargo institucional formal associado ao servidor.

#### `EmpresaInstituicao`
Representa a empresa ou instituição associada a vínculos terceirizados.

#### `Servidor`
Representa o perfil institucional formal de servidor vinculado a um usuário.

#### `Terceirizado`
Representa o perfil institucional formal de terceirizado vinculado a um usuário e a uma empresa/instituição.

---

## 2. Regras centrais do domínio

Esta milestone deve consolidar, na medida do possível, as seguintes regras:

- `Cargo` é exclusivo de `Servidor`;
- `Servidor` depende de um `Usuario` já existente;
- `Terceirizado` depende de um `Usuario` já existente;
- `Terceirizado` deve estar associado a `EmpresaInstituicao`;
- o domínio deve preparar e permitir a consolidação de regras institucionais usadas por outros domínios.

### Observação importante sobre integração com Organizacional

Ao final desta milestone, o sistema deve estar apto a consolidar a regra de elegibilidade institucional do responsável do setor, em conjunto com o domínio `Organizacional`.

Ou seja, esta milestone não existe isoladamente: ela fecha uma dependência importante aberta pela milestone organizacional.

---

## 3. Camadas do domínio

Cada app interno do domínio deve seguir a arquitetura do projeto, incluindo:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`
- `tests.py`

Se fizer sentido, também pode incluir:
- `choices.py`

---

## O que entra

A Milestone 3 pode incluir:

- criação física do módulo `PessoasInstitucionais/`;
- criação dos apps internos previstos;
- implementação dos models centrais do domínio;
- implementação das camadas `business`, `rules` e `helpers`;
- implementação de serializers, views e urls dos apps internos;
- documentação Swagger dos endpoints implementados;
- testes dos apps internos, conforme o padrão atual do projeto;
- integração com `Identidade`;
- integração necessária com `Organizacional` para consolidar regras dependentes de perfil institucional.

---

## O que não entra

Esta milestone **não deve** incluir:

- implementação do domínio `Academico`;
- `Aluno`;
- `Curso`;
- `AlunoCurso`;
- qualquer refactor amplo fora do domínio e das integrações estritamente necessárias;
- ampliação arbitrária de escopo além dos perfis institucionais formais.

---

## Decisões já consolidadas que esta milestone deve respeitar

1. O sistema é organizado por domínio.
2. Os domínios são módulos agregadores, não apps únicos.
3. Os apps internos devem ser finos e, em regra, cada app corresponde a um model principal.
4. O módulo desta milestone deve ser `PessoasInstitucionais/`.
5. O projeto segue arquitetura em camadas.
6. Views devem permanecer leves.
7. `Cargo` e `Funcao` são conceitos diferentes.
8. `Servidor` e `Terceirizado` dependem da identidade já existente do usuário.
9. Não misturar inglês e português em nomes de métodos, funções e variáveis do domínio, exceto nas convenções obrigatórias do framework.

---

## Ordem interna recomendada da milestone

## Etapa 3.1 — App `cargos`

### Objetivo
Criar a base institucional de cargos formais.

### Inclui
- app `PessoasInstitucionais/cargos/`
- model `Cargo`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar cargos formais de maneira coerente e isolada.

---

## Etapa 3.2 — App `empresas_instituicoes`

### Objetivo
Criar a base institucional para vínculos terceirizados.

### Inclui
- app `PessoasInstitucionais/empresas_instituicoes/`
- model `EmpresaInstituicao`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar as entidades institucionais externas necessárias aos terceirizados.

---

## Etapa 3.3 — App `servidores`

### Objetivo
Formalizar o perfil institucional de servidor.

### Inclui
- app `PessoasInstitucionais/servidores/`
- model `Servidor`
- vínculo com `Usuario`
- vínculo com `Cargo`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar usuários que sejam formalmente servidores.

---

## Etapa 3.4 — App `terceirizados`

### Objetivo
Formalizar o perfil institucional de terceirizado.

### Inclui
- app `PessoasInstitucionais/terceirizados/`
- model `Terceirizado`
- vínculo com `Usuario`
- vínculo com `EmpresaInstituicao`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar usuários terceirizados com vínculo institucional externo.

---

## Etapa 3.5 — Integração interna do domínio

### Objetivo
Consolidar a coerência entre os apps internos do domínio.

### Inclui
- revisão das relações entre `Cargo`, `EmpresaInstituicao`, `Servidor` e `Terceirizado`;
- revisão das rotas agregadas do módulo;
- validação estrutural do domínio;
- revisão da documentação local impactada.

### Critério de saída
O domínio `PessoasInstitucionais` deve ficar internamente coerente e pronto para integração interdomínio.

---

## Etapa 3.6 — Integração com `Organizacional`

### Objetivo
Consolidar regras organizacionais dependentes de perfil institucional.

### Inclui
- integração com o domínio `Organizacional`;
- consolidação da elegibilidade institucional do responsável do setor;
- validação das invariantes cruzadas necessárias.

### Critério de saída
A dependência aberta na milestone organizacional deve ficar resolvida de forma coerente.

---

## Critérios de aceite da milestone

A Milestone 3 só deve ser considerada concluída quando:

### 1. O domínio estiver fisicamente criado
- módulo `PessoasInstitucionais/`
- apps internos previstos

### 2. Os models centrais estiverem implementados
- `Cargo`
- `EmpresaInstituicao`
- `Servidor`
- `Terceirizado`

### 3. O domínio respeitar a arquitetura em camadas
- lógica principal fora de views;
- estrutura coerente com o padrão do projeto.

### 4. As regras centrais do domínio estiverem refletidas
- `Cargo` exclusivo de `Servidor`;
- `Servidor` e `Terceirizado` vinculados a `Usuario`;
- `Terceirizado` vinculado a `EmpresaInstituicao`.

### 5. A integração necessária com `Organizacional` estiver consolidada
- especialmente a regra institucional do responsável de setor.

### 6. Os testes previstos para os apps internos estiverem implementados
- conforme o padrão atual do projeto.

---

## Riscos da milestone

## 1. Misturar `Cargo` com `Funcao`
Isso quebraria uma distinção conceitual já consolidada.

## 2. Acoplar demais o domínio institucional ao organizacional
O domínio deve integrar, não se dissolver no outro.

## 3. Implementar perfis institucionais sem respeitar a identidade existente
`Servidor` e `Terceirizado` devem depender de `Usuario`.

## 4. Expandir escopo para o domínio acadêmico cedo demais
Isso deve ficar para a próxima milestone.

---

## Arquivos impactados prioritariamente

Espera-se impacto principalmente em:

- criação do módulo `PessoasInstitucionais/`
- criação dos apps internos previstos
- `Cortex/settings.py`
- `Cortex/urls.py`
- documentação estrutural e checklist, se necessário

---

## Saídas esperadas

Ao final da milestone, espera-se ter:

- módulo `PessoasInstitucionais/` criado;
- apps `cargos`, `empresas_instituicoes`, `servidores` e `terceirizados` implementados;
- camadas dos apps estruturadas;
- exposição básica via API;
- testes básicos do domínio;
- integração suficiente com `Organizacional` para consolidar regras institucionais pendentes.

---

## Próximo passo após esta milestone

Após a conclusão e revisão da Milestone 3, o próximo passo deve ser:

- elaborar o plano da **Milestone 4 — Domínio Acadêmico**

---

## Resumo executivo

A Milestone 3 implementa o domínio `PessoasInstitucionais`, responsável por representar perfis institucionais formais do usuário.

Ela consolida cargos, empresas/instituições, servidores e terceirizados, além de fechar dependências importantes abertas pela milestone organizacional.