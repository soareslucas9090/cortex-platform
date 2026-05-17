# Visão Geral do Produto e do Sistema

## Objetivo

Este documento apresenta uma visão geral do Cortex como produto e como sistema, consolidando:

- o propósito inicial da aplicação;
- os principais conceitos de domínio já identificados;
- a estratégia arquitetural adotada;
- a direção técnica que guiará a implementação.

Ele deve funcionar como documento de entrada para quem precisa entender rapidamente:

- o que o sistema pretende resolver;
- como ele está sendo organizado;
- e quais fundamentos técnicos já foram definidos.

---

## Visão geral do produto

O Cortex é um sistema backend estruturado para apoiar a modelagem e operação de um contexto institucional/acadêmico, com foco inicial em:

- identidade de usuários;
- vínculos organizacionais com setores;
- perfis institucionais;
- vínculos acadêmicos.

Seu núcleo gira em torno de uma entidade central de usuário, sobre a qual diferentes perfis e vínculos são construídos.

O sistema foi pensado para organizar esses dados e comportamentos de forma explícita, modular e coerente com o domínio, evitando que a implementação cresça de forma desordenada desde o início.

---

## Problema que o sistema resolve

Na prática, o sistema precisa representar de forma consistente:

- quem são os usuários;
- quais perfis eles possuem;
- como eles se vinculam à instituição;
- com quais setores eles se relacionam;
- quais funções exercem nesses setores;
- como alunos, servidores e terceirizados convivem no mesmo ecossistema.

Isso exige uma modelagem capaz de diferenciar corretamente conceitos que, embora próximos, não são iguais, como por exemplo:

- `Cargo` e `Funcao`
- perfil acadêmico e atuação organizacional
- identidade base e especializações institucionais

---

## Visão geral do domínio

Até o momento, o sistema foi dividido em quatro domínios principais:

### `Identidade`

Responsável por:

- `Usuario`
- `Contato`
- `Endereco`
- `Matricula`

### `Organizacional`

Responsável por:

- `Setor`
- `Funcao`
- `SetorVinculo`

### `PessoasInstitucionais`

Responsável por:

- `Servidor`
- `Cargo`
- `Terceirizado`
- `EmpresaInstituicao`

### `Academico`

Responsável por:

- `Aluno`
- `Curso`
- `AlunoCurso`

---

## Conceitos centrais já consolidados

### `Usuario` como centro da identidade

Todo perfil do sistema parte de `Usuario`.

### `Cargo` e `Funcao` são conceitos diferentes

- `Cargo`: posição formal do servidor
- `Funcao`: papel exercido em um setor

### `SetorVinculo` é entidade de negócio

Não é apenas uma tabela associativa entre usuário e setor.

### Monitoria é função

O conceito de monitor não deve existir como atributo booleano solto. Ele deve ser representado por uma `Funcao`.

### Responsabilidade de setor nasce do vínculo

Todo setor precisa ter um responsável, e esse responsável precisa ser um servidor vinculado ao setor com uma função.

---

## Estratégia arquitetural

A estratégia adotada para o Cortex é:

### 1. Modularização por domínio

O sistema será organizado por contexto de negócio, e não apenas por agrupamento técnico.

### 2. Arquitetura em camadas

Cada domínio deve seguir a arquitetura já utilizada na base do projeto:

- `models.py`
- `business.py`
- `rules.py`
- `helpers.py`
- `serializers.py`
- `views.py`
- `urls.py`

### 3. Views leves

As views devem receber a requisição, validar serializer e delegar a lógica à camada de business.

### 4. Regras explícitas

As invariantes do domínio devem ficar principalmente em:

- `rules.py`
- `business.py`

### 5. Base reutilizável

O sistema aproveitará uma base técnica já existente, especialmente por meio do `AppCore`, desde que revisada e ajustada conforme necessário.

---

## Estrutura inicial prevista do sistema

O projeto deve evoluir inicialmente com os seguintes apps Django:

- `identidade`
- `organizacional`
- `pessoas_institucionais`
- `academico`

Além disso, o sistema já possui uma base composta por:

- `AppCore/` — infraestrutura reutilizável
- `Auth/` — autenticação customizável do projeto
- `Cortex/` — configuração central do Django

---

## Ordem inicial recomendada de implementação

A ordem de implementação definida até o momento é:

1. `identidade`
2. `organizacional`
3. `pessoas_institucionais`
4. `academico`

### Motivo

Essa ordem respeita a dependência natural entre os domínios:

- primeiro a identidade;
- depois a estrutura organizacional;
- depois os perfis institucionais;
- por fim os vínculos acadêmicos.

---

## Regras importantes já conhecidas

Algumas regras já definidas e importantes para a visão geral do sistema são:

- login por CPF;
- `Cargo` só existe para `Servidor`;
- `EmpresaInstituicao` será usada, neste estágio, apenas para `Terceirizado`;
- todo vínculo com setor exige função;
- um usuário pode ter múltiplos vínculos com setores;
- todo setor deve possuir responsável válido;
- monitoria é tratada no domínio organizacional;
- aluno monitor deve estar vinculado a setor.

---

## Documentos que detalham esta visão

Esta visão geral é complementada pelos seguintes documentos:

- `docs/diagrams/02-bounded-contexts.md`
- `docs/diagrams/03-core-erd.md`
- `docs/diagrams/04-aggregates-and-invariants.md`
- `docs/decisions/ADR-001-modularizacao-por-dominio.md`
- `docs/project/django-project-tree.md`

---

## Próximo passo previsto

O próximo passo planejado do projeto é uma **revisão geral do `AppCore`**, com objetivo de verificar se a base técnica atual está realmente pronta para sustentar a modelagem do Cortex.

Essa revisão deverá observar principalmente:

- modelo base de usuário;
- autenticação por CPF;
- mixins de business/helpers/rules/state;
- views base;
- permissões;
- exceptions;
- paginação;
- consistência das convenções da base.

---

## O que este documento não tenta fazer

Este documento não detalha:

- todos os atributos de cada entidade;
- todas as regras de negócio específicas;
- todas as rotas da API;
- detalhes finos de implementação.

Esses pontos pertencem a artefatos mais específicos.

---

## Resumo executivo

O Cortex está sendo estruturado como um backend modular, orientado por domínio, com `Usuario` no centro da identidade e com forte ênfase em vínculos organizacionais, perfis institucionais e vínculos acadêmicos.

A direção arquitetural atual busca:

- clareza de domínio;
- crescimento incremental;
- reutilização da base técnica existente;
- e disciplina na separação entre view, business e regras.

O próximo passo natural é revisar o `AppCore` para garantir que a fundação técnica esteja alinhada com essa visão.
