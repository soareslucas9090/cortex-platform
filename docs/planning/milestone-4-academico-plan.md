# Plano da Milestone 4 — Domínio Acadêmico

## Objetivo

A Milestone 4 existe para implementar o domínio `Academico` do Cortex.

Esse domínio deve representar os perfis e vínculos acadêmicos do sistema, consolidando a modelagem de alunos, cursos e vínculos acadêmicos formais.

Ao final desta milestone, o projeto deve possuir uma implementação coerente para:

- `Curso`
- `Aluno`
- `AlunoCurso`

---

## Resultado esperado ao final da milestone

Ao final da Milestone 4, o sistema deve estar apto a:

1. cadastrar e manter cursos;
2. representar usuários que sejam alunos;
3. representar o vínculo acadêmico entre aluno e curso;
4. consolidar a base acadêmica formal do sistema;
5. preparar o terreno para integrações futuras sem misturar regra acadêmica com regra organizacional.

---

## Estrutura do domínio

### Módulo de domínio
- `Academico/`

### Apps internos previstos
- `cursos/`
- `alunos/`
- `aluno_cursos/`

---

## Escopo da milestone

## 1. Models do domínio

Esta milestone deve incluir os seguintes models principais:

- `Curso`
- `Aluno`
- `AlunoCurso`

### Papel de cada model

#### `Curso`
Representa um curso formal da instituição.

#### `Aluno`
Representa o perfil acadêmico de aluno vinculado a um usuário do sistema.

#### `AlunoCurso`
Representa o vínculo acadêmico entre aluno e curso.

---

## 2. Regras centrais do domínio

Esta milestone deve consolidar, na medida do possível, as seguintes regras:

- `Aluno` depende de um `Usuario` já existente;
- `AlunoCurso` depende de `Aluno` e `Curso`;
- o domínio acadêmico deve representar vínculos acadêmicos formais, sem absorver responsabilidades do domínio organizacional;
- monitoria não deve ser tratada como atributo acadêmico isolado.

### Observação importante sobre monitoria

A monitoria deve continuar sendo tratada no domínio `Organizacional`, por meio de vínculo organizacional e função apropriada.

Portanto, esta milestone não deve modelar monitoria como campo isolado em `Aluno` ou `AlunoCurso`, salvo se a documentação atual do projeto exigir explicitamente outra solução — e, nesse caso, a divergência deve ser explicada antes da implementação.

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

A Milestone 4 pode incluir:

- criação física do módulo `Academico/`;
- criação dos apps internos previstos;
- implementação dos models centrais do domínio;
- implementação das camadas `business`, `rules` e `helpers`;
- implementação de serializers, views e urls dos apps internos;
- documentação Swagger dos endpoints implementados;
- testes dos apps internos, conforme o padrão atual do projeto;
- integração com `Identidade`;
- integração interna entre os apps do domínio acadêmico.

---

## O que não entra

Esta milestone **não deve** incluir:

- remodelagem da monitoria como regra acadêmica;
- duplicação de regras já pertencentes ao domínio `Organizacional`;
- criação de novos domínios;
- refactor amplo fora do domínio acadêmico e das integrações mínimas necessárias;
- ampliação arbitrária de escopo além dos perfis acadêmicos formais.

---

## Decisões já consolidadas que esta milestone deve respeitar

1. O sistema é organizado por domínio.
2. Os domínios são módulos agregadores, não apps únicos.
3. Os apps internos devem ser finos e, em regra, cada app corresponde a um model principal.
4. O módulo desta milestone deve ser `Academico/`.
5. O projeto segue arquitetura em camadas.
6. Views devem permanecer leves.
7. `Aluno` depende da identidade já existente do usuário.
8. `AlunoCurso` é vínculo acadêmico formal.
9. Monitoria pertence ao domínio organizacional, não ao acadêmico.
10. Não misturar inglês e português em nomes de métodos, funções e variáveis do domínio, exceto nas convenções obrigatórias do framework.

---

## Ordem interna recomendada da milestone

## Etapa 4.1 — App `cursos`

### Objetivo
Criar a base formal dos cursos.

### Inclui
- app `Academico/cursos/`
- model `Curso`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar cursos de maneira coerente e isolada.

---

## Etapa 4.2 — App `alunos`

### Objetivo
Formalizar o perfil acadêmico do aluno.

### Inclui
- app `Academico/alunos/`
- model `Aluno`
- vínculo com `Usuario`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar usuários que sejam formalmente alunos.

---

## Etapa 4.3 — App `aluno_cursos`

### Objetivo
Formalizar o vínculo acadêmico entre aluno e curso.

### Inclui
- app `Academico/aluno_cursos/`
- model `AlunoCurso`
- vínculo com `Aluno`
- vínculo com `Curso`
- camadas do app
- endpoints mínimos
- testes do app

### Critério de saída
O sistema deve conseguir representar vínculos acadêmicos formais entre aluno e curso.

---

## Etapa 4.4 — Integração interna do domínio

### Objetivo
Consolidar a coerência entre os apps internos do domínio.

### Inclui
- revisão das relações entre `Curso`, `Aluno` e `AlunoCurso`;
- revisão das rotas agregadas do módulo;
- validação estrutural do domínio;
- revisão da documentação local impactada.

### Critério de saída
O domínio `Academico` deve ficar internamente coerente e pronto para integração futura com os demais domínios.

---

## Critérios de aceite da milestone

A Milestone 4 só deve ser considerada concluída quando:

### 1. O domínio estiver fisicamente criado
- módulo `Academico/`
- apps internos previstos

### 2. Os models centrais estiverem implementados
- `Curso`
- `Aluno`
- `AlunoCurso`

### 3. O domínio respeitar a arquitetura em camadas
- lógica principal fora de views;
- estrutura coerente com o padrão do projeto.

### 4. As regras centrais do domínio estiverem refletidas
- `Aluno` vinculado a `Usuario`;
- `AlunoCurso` vinculado a `Aluno` e `Curso`;
- monitoria não duplicada indevidamente no domínio acadêmico.

### 5. Os testes previstos para os apps internos estiverem implementados
- conforme o padrão atual do projeto.

### 6. A integração interna do domínio estiver validada
- rotas, dependências e coerência estrutural.

---

## Riscos da milestone

## 1. Misturar regra acadêmica com regra organizacional
Isso pode causar duplicação de responsabilidades.

## 2. Modelar monitoria como atributo acadêmico isolado
Isso contraria a decisão atual do projeto.

## 3. Implementar vínculo acadêmico sem respeitar a identidade já existente
`Aluno` deve depender de `Usuario`.

## 4. Expandir escopo além do domínio acadêmico
Esta milestone deve permanecer focada.

---

## Arquivos impactados prioritariamente

Espera-se impacto principalmente em:

- criação do módulo `Academico/`
- criação dos apps internos previstos
- `Cortex/settings.py`
- `Cortex/urls.py`
- documentação estrutural e checklist, se necessário

---

## Saídas esperadas

Ao final da milestone, espera-se ter:

- módulo `Academico/` criado;
- apps `cursos`, `alunos` e `aluno_cursos` implementados;
- camadas dos apps estruturadas;
- exposição básica via API;
- testes básicos do domínio;
- integração interna suficiente para representar formalmente o domínio acadêmico.

---

## Próximo passo após esta milestone

Após a conclusão e revisão da Milestone 4, o próximo passo deve ser:

- seguir para a etapa de integração e consolidação final do projeto.

---

## Resumo executivo

A Milestone 4 implementa o domínio `Academico`, responsável por representar perfis e vínculos acadêmicos formais do sistema.

Ela consolida cursos, alunos e vínculos acadêmicos, preservando a separação entre regra acadêmica e regra organizacional.