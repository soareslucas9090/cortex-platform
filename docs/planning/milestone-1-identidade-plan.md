# Plano da Milestone 1 — Domínio Identidade

## Objetivo

A Milestone 1 existe para implementar o primeiro domínio real do Cortex: `Identidade`.

Esse domínio deve consolidar a base concreta de identidade do sistema, criando o usuário real do projeto e os relacionamentos centrais associados a ele.

Ao final desta milestone, o sistema deve possuir um domínio `identidade` capaz de sustentar:

- o `Usuario` concreto do projeto;
- os dados básicos de contato;
- os dados de endereço;
- os registros de matrícula vinculados ao usuário;
- a integração correta entre autenticação e o modelo de usuário real.

---

## Resultado esperado ao final da milestone

Ao final da Milestone 1, o projeto deve estar apto a:

1. possuir um model concreto `Usuario`;
2. utilizar esse model como base de autenticação do sistema;
3. persistir e consultar dados centrais de identidade;
4. manter a base pronta para servir de apoio aos domínios seguintes;
5. expor os primeiros componentes do domínio `identidade` de forma coerente com a arquitetura do projeto.

---

## Escopo da milestone

## 1. Modelos do domínio

Esta milestone deve incluir os seguintes modelos:

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`

### Papel de cada modelo

#### `Usuario`

Entidade central de identidade do sistema.

Deve concentrar:

- dados centrais de autenticação;
- dados básicos da pessoa;
- relação com os demais perfis futuros do sistema.

#### `Contato`

Representa dados de contato associados ao usuário.

#### `Endereco`

Representa dados de endereço associados ao usuário.

#### `Matricula`

Representa identificadores institucionais/acadêmicos vinculados ao usuário.

---

## 2. Manager concreto do usuário

A milestone deve incluir um manager concreto para `Usuario`, responsável por:

- normalizar email;
- normalizar CPF;
- criar usuário comum;
- criar superusuário;
- manter coerência com a estratégia de autenticação definida anteriormente.

---

## 3. Integração com autenticação

A milestone deve consolidar a integração do usuário concreto com a autenticação do projeto.

Isso inclui:

- preparar o model `Usuario` para funcionar corretamente com a autenticação definida na fundação;
- alinhar o `AUTH_USER_MODEL` ao domínio `identidade`;
- garantir coerência entre o domínio `Identidade` e o fluxo de login já preparado na Milestone 0.

---

## 4. Camadas do domínio

O app `identidade` deve seguir a arquitetura do projeto, incluindo:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

O objetivo é evitar concentração de lógica em serializers ou views.

---

## O que entra

A Milestone 1 pode incluir:

- criação física do app `identidade`;
- implementação do model `Usuario`;
- implementação dos models `Contato`, `Endereco` e `Matricula`;
- criação do manager concreto do usuário;
- integração com `AUTH_USER_MODEL`;
- criação das classes base de `business`, `rules`, `helpers`, serializers, views e urls do domínio;
- endpoints básicos do domínio, se a implementação for dividida até esse ponto.

---

## O que não entra

Esta milestone **não deve** incluir:

- `Setor`, `Funcao`, `SetorVinculo`;
- `Servidor`, `Cargo`, `Terceirizado`, `EmpresaInstituicao`;
- `Aluno`, `Curso`, `AlunoCurso`;
- regras organizacionais;
- monitoria;
- responsabilidade de setor;
- regras cruzadas com domínios ainda não implementados;
- seeds avançados;
- integrações profundas com domínios futuros;
- qualquer ampliação de escopo para além de `Identidade`.

---

## Decisões já consolidadas que esta milestone deve respeitar

1. O sistema é organizado por domínio.
2. O app Django deste domínio deve se chamar `identidade`.
3. O projeto segue arquitetura em camadas.
4. Views devem permanecer leves.
5. O usuário concreto do sistema pertence ao domínio `Identidade`.
6. O login do sistema deve permanecer compatível com a estratégia definida anteriormente.
7. CPF e email devem ser tratados com normalização adequada.
8. A base do `AppCore` deve ser reutilizada sempre que fizer sentido, sem forçar acoplamento indevido.

---

## Ordem interna recomendada da milestone

## Etapa 1.1 — Models e manager

### Objetivo

Criar a estrutura central do domínio.

### Inclui

- app `identidade`
- model `Usuario`
- model `Contato`
- model `Endereco`
- model `Matricula`
- manager concreto do usuário
- integração inicial com autenticação

### Critério de saída

A estrutura de dados do domínio deve estar estável o suficiente para sustentar regras e endpoints.

---

## Etapa 1.2 — Business, Rules e Helpers

### Objetivo

Consolidar a lógica do domínio fora de views e serializers.

### Inclui

- regras de criação e atualização;
- regras de validação;
- helpers de consulta explícita;
- organização da lógica do domínio conforme a arquitetura do projeto.

### Critério de saída

A lógica principal do domínio deve estar fora das views e preparada para reutilização.

---

## Etapa 1.3 — Serializers, Views e URLs

### Objetivo

Expor o domínio de forma coerente via API.

### Inclui

- serializers de entrada e saída;
- views seguindo as classes base do projeto;
- urls do app;
- documentação Swagger dos endpoints implementados.

### Critério de saída

O domínio deve ter exposição básica coerente com a arquitetura do projeto.

---

## Critérios de aceite da milestone

A Milestone 1 só deve ser considerada concluída quando:

### 1. O usuário concreto do sistema estiver implementado

- `Usuario` existe como model concreto;
- autenticação já consegue se apoiar nesse model.

### 2. Os modelos centrais de identidade estiverem implementados

- `Contato`
- `Endereco`
- `Matricula`

### 3. O domínio respeitar a arquitetura em camadas

- lógica principal fora de views;
- estrutura coerente com o padrão do projeto.

### 4. O projeto ficar pronto para os próximos domínios

- `Identidade` deve servir como base para `Organizacional`, `PessoasInstitucionais` e `Academico`.

---

## Riscos da milestone

## 1. Escopo excessivo

O agente pode tentar implementar regras de outros domínios junto com `Identidade`.

## 2. Modelagem apressada

O agente pode assumir campos, cardinalidades ou relações sem respeitar a documentação já produzida.

## 3. Acoplamento indevido com infraestrutura

O agente pode espalhar lógica de domínio em serializers, views ou configurações genéricas.

## 4. Misturar autenticação e domínio de forma desorganizada

É importante integrar `Usuario` com auth sem transformar o domínio numa extensão desordenada da infraestrutura.

---

## Arquivos impactados prioritariamente

Espera-se impacto principalmente em:

- criação do app `identidade/`
- `Cortex/settings.py`
- possivelmente `Cortex/urls.py`
- pontos da autenticação que precisem ser conectados ao model concreto

---

## Saídas esperadas

Ao final da milestone, espera-se ter:

- app `identidade` criado;
- `Usuario` concreto implementado;
- `Contato`, `Endereco` e `Matricula` implementados;
- integração do usuário com autenticação consolidada;
- base pronta para avanço aos próximos domínios.

---

## Próximo passo após esta milestone

Após a conclusão e revisão da Milestone 1, o próximo passo deve ser:

- elaborar o plano da **Milestone 2 — Domínio Organizacional**

---

## Resumo executivo

A Milestone 1 implementa o domínio `Identidade`, que é a base concreta do Cortex.

Ela é responsável por consolidar o usuário real do sistema e seus relacionamentos centrais, preparando o projeto para a evolução segura dos domínios seguintes.
