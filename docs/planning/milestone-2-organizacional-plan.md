# Plano da Milestone 2 — Domínio Organizacional

## Objetivo

A Milestone 2 existe para implementar o domínio `Organizacional` do Cortex.

Esse domínio deve modelar a estrutura institucional e os vínculos funcionais entre usuários, setores e funções, consolidando a base organizacional do sistema.

Ao final desta milestone, o projeto deve possuir uma implementação coerente para:

- `Setor`
- `Funcao`
- `SetorVinculo`

além das regras centrais ligadas ao vínculo organizacional.

---

## Resultado esperado ao final da milestone

Ao final da Milestone 2, o sistema deve estar apto a:

1. cadastrar e manter setores;
2. cadastrar e manter funções organizacionais;
3. vincular usuários a setores com função obrigatória;
4. permitir múltiplos vínculos organizacionais por usuário;
5. representar monitoria como função;
6. preparar a base para a futura consolidação da regra de responsável de setor em conjunto com perfis institucionais.

---

## Escopo da milestone

## 1. Modelos do domínio

Esta milestone deve incluir os seguintes modelos:

- `Setor`
- `Funcao`
- `SetorVinculo`

### Papel de cada modelo

#### `Setor`

Representa uma unidade organizacional da instituição.

#### `Funcao`

Representa o papel exercido por um usuário em determinado setor.

Deve contemplar o atributo:

- `e_gratificada`

#### `SetorVinculo`

Representa o vínculo entre usuário, setor e função.

Esse model não deve ser tratado como simples tabela associativa. Ele é uma entidade de negócio do domínio organizacional.

---

## 2. Regras centrais do domínio

Esta milestone deve consolidar, na medida do possível, as seguintes regras:

- todo vínculo com setor exige função;
- um usuário pode possuir múltiplos vínculos com setores;
- monitoria deve ser representada como função;
- `Funcao` deve possuir `e_gratificada`;
- o domínio deve estar preparado para a regra de responsável de setor.

### Observação importante sobre responsável de setor

A regra completa “responsável deve ser servidor” depende do domínio `PessoasInstitucionais`, que ainda não estará implementado nesta milestone.

Portanto, nesta etapa:

- a estrutura organizacional deve ser preparada para representar a responsabilidade do vínculo;
- a validação completa de elegibilidade do responsável poderá ser consolidada posteriormente, quando o domínio institucional existir.

---

## 3. Camadas do domínio

O app `organizacional` deve seguir a arquitetura do projeto, incluindo:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

Se fizer sentido, também pode incluir:

- `choices.py`

---

## O que entra

A Milestone 2 pode incluir:

- criação física do módulo `Organizacional/` e do app `organizacional`;
- implementação dos models `Setor`, `Funcao` e `SetorVinculo`;
- implementação das camadas `business`, `rules` e `helpers`;
- implementação dos serializers, views e urls do domínio;
- documentação Swagger dos endpoints implementados;
- integração do domínio `Organizacional` com o domínio `Identidade` já existente.

---

## O que não entra

Esta milestone **não deve** incluir:

- implementação do domínio `PessoasInstitucionais`;
- `Servidor`;
- `Cargo`;
- `Terceirizado`;
- `EmpresaInstituicao`;
- implementação do domínio `Academico`;
- `Aluno`;
- `Curso`;
- `AlunoCurso`;
- validação completa da elegibilidade institucional do responsável de setor;
- regras cruzadas profundas com domínios ainda não implementados;
- qualquer ampliação de escopo para além do domínio `Organizacional`.

---

## Decisões já consolidadas que esta milestone deve respeitar

1. O sistema é organizado por domínio.
2. Os apps ficam dentro de módulos de domínio.
3. O módulo desta milestone deve ser `Organizacional/`.
4. O app Django desta milestone deve ser `organizacional`.
5. O projeto segue arquitetura em camadas.
6. Views devem permanecer leves.
7. `SetorVinculo` é entidade de negócio, não apenas tabela associativa.
8. `monitor` deve ser representado como função.
9. `Cargo` e `Funcao` são conceitos diferentes.
10. Não misturar inglês e português em nomes de métodos, funções e variáveis do domínio, exceto nas convenções obrigatórias do framework.

---

## Ordem interna recomendada da milestone

## Etapa 2.1 — Models

### Objetivo

Criar a estrutura central do domínio.

### Inclui

- módulo `Organizacional/`
- app `organizacional`
- model `Setor`
- model `Funcao`
- model `SetorVinculo`

### Critério de saída

A estrutura de dados do domínio deve estar pronta para sustentar as regras do vínculo organizacional.

---

## Etapa 2.2 — Business, Rules e Helpers

### Objetivo

Consolidar a lógica do domínio fora de views e serializers.

### Inclui

- validação de função obrigatória;
- organização da lógica de criação e manutenção dos vínculos;
- helpers explícitos para consultas do domínio;
- tratamento coerente da semântica de responsabilidade no vínculo, sem antecipar validação institucional completa.

### Critério de saída

A lógica principal do domínio organizacional deve estar estruturada nas camadas corretas.

---

## Etapa 2.3 — Serializers, Views e URLs

### Objetivo

Expor o domínio via API de forma coerente.

### Inclui

- serializers de entrada e saída;
- views baseadas na arquitetura do projeto;
- urls do app;
- documentação Swagger dos endpoints implementados.

### Critério de saída

O domínio organizacional deve estar exposto de forma mínima e coerente via API.

---

## Critérios de aceite da milestone

A Milestone 2 só deve ser considerada concluída quando:

### 1. O domínio organizacional estiver fisicamente criado

- módulo `Organizacional/`
- app `organizacional`

### 2. Os modelos centrais estiverem implementados

- `Setor`
- `Funcao`
- `SetorVinculo`

### 3. O domínio respeitar a arquitetura em camadas

- lógica principal fora de views;
- estrutura coerente com o padrão do projeto.

### 4. As regras centrais já estiverem refletidas no domínio

- função obrigatória no vínculo;
- monitoria como função;
- `e_gratificada` em `Funcao`;
- múltiplos vínculos por usuário.

### 5. A base ficar pronta para integração futura com `PessoasInstitucionais`

- sem gambiarras para simular `Servidor`;
- sem fechar prematuramente regras que dependem de domínio ainda inexistente.

---

## Riscos da milestone

## 1. Escopo excessivo

O agente pode tentar adiantar a implementação de `Servidor`, `Cargo` ou regras institucionais completas.

## 2. Tratar `SetorVinculo` como tabela simples

Isso enfraquece a modelagem do domínio organizacional.

## 3. Misturar `Cargo` e `Funcao`

Esses conceitos devem permanecer distintos.

## 4. Tentar validar cedo demais a elegibilidade do responsável

A regra completa depende do domínio `PessoasInstitucionais`.

---

## Arquivos impactados prioritariamente

Espera-se impacto principalmente em:

- criação do módulo `Organizacional/`
- criação do app `organizacional`
- `Cortex/settings.py`
- `Cortex/urls.py`

---

## Saídas esperadas

Ao final da milestone, espera-se ter:

- módulo `Organizacional/organizacional` criado;
- `Setor`, `Funcao` e `SetorVinculo` implementados;
- camadas do domínio organizacional estruturadas;
- exposição básica via API;
- base pronta para integração futura com `PessoasInstitucionais` e `Academico`.

---

## Próximo passo após esta milestone

Após a conclusão e revisão da Milestone 2, o próximo passo deve ser:

- elaborar o plano da **Milestone 3 — Domínio PessoasInstitucionais**

---

## Resumo executivo

A Milestone 2 implementa o domínio `Organizacional`, responsável por modelar setores, funções e vínculos organizacionais dos usuários.

Ela é a base para representar a atuação institucional dos usuários no sistema e prepara o terreno para a consolidação posterior das regras ligadas a perfis institucionais e monitoria.
