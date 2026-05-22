# Usuários de Teste e Cenários de Seed do Cortex

## Objetivo

Este documento define usuários de teste, cenários iniciais de seed e situações de negócio mínimas para validar a modelagem central do Cortex.

Ele serve para:

- guiar a criação de massa inicial;
- validar regras críticas do domínio;
- facilitar testes manuais e integração inicial;
- apoiar demonstrações e desenvolvimento incremental.

---

## Princípios

1. Os cenários devem refletir o domínio real.
2. A massa inicial deve ser pequena, mas expressiva.
3. Cada seed deve validar ao menos uma regra importante.
4. Os cenários devem cobrir:
   - identidade;
   - estrutura organizacional;
   - perfis institucionais;
   - perfis acadêmicos;
   - vínculos entre domínios.

---

# 1. Dados mestres mínimos

## 1.1 Setores

Sugestão de seed inicial mínima:

- `DENS`
- `DIAP`
- `CODIS`
- `CCTI`
- `NAPNE/FLO`

### Objetivo

Permitir cenários com:

- setor administrativo;
- setor acadêmico;
- coordenação;
- monitoria;
- responsabilidade formal.

---

## 1.2 Funções

Sugestão de seed inicial mínima:

- `DIRETOR`
- `COORDENADOR`
- `CHEFE`
- `MONITOR`
- `MEMBRO`

### Campos importantes

- `sigla`
- `descricao`
- `e_gratificada`
- `ativo`

### Objetivo

Cobrir:

- responsabilidade de setor;
- vínculo funcional simples;
- vínculo de monitoria;
- função gratificada e não gratificada.

---

## 1.3 Cargos

Sugestão de seed inicial mínima:

- `PROFESSOR EBTT`
- `ASSISTENTE EM ADMINISTRACAO`
- `TECNICO DE TECNOLOGIA DA INFORMACAO`

### Objetivo

Cobrir:

- servidor docente;
- servidor técnico administrativo;
- cenário de responsável de setor com diferentes cargos.

---

## 1.4 Empresas

Sugestão de seed inicial mínima:

- `EMPRESA LIMPEZA IFPI`
- `EMPRESA VIGILANCIA IFPI`

### Objetivo

Cobrir terceirização básica.

---

## 1.5 Cursos

Sugestão de seed inicial mínima:

- `Análise e Desenvolvimento de Sistemas`
- `Licenciatura em Matemática`
- `Técnico em Informática`

### Objetivo

Cobrir cenários acadêmicos básicos.

---

# 2. Usuários de teste sugeridos

## 2.1 Servidor docente responsável por setor

### Perfil

Usuário servidor docente, com cargo formal e responsabilidade por setor.

### Dados sugeridos

- `cpf`: `11111111111`
- `nome`: `Professor Responsavel`
- perfil: `Servidor`
- cargo: `PROFESSOR EBTT`
- vínculo com setor (no `SetorVinculo`):
  - setor: `CODIS`
  - função: `COORDENADOR`
  - responsavel: `True`

### Regra validada

- setor com responsável servidor
- vínculo com função obrigatória

---

## 2.2 Servidor técnico com múltiplos vínculos

### Perfil

Servidor técnico vinculado a mais de um setor.

### Dados sugeridos

- `cpf`: `22222222222`
- `nome`: `Tecnico MultiSetor`
- perfil: `Servidor`
- cargo: `TECNICO DE TECNOLOGIA DA INFORMACAO`
- vínculos com setores (em múltiplos `SetorVinculo`):
  - setor: `CCTI`, função: `CHEFE`, responsavel: `False`
  - setor: `DIAP`, função: `MEMBRO`, responsavel: `False`

### Regra validada

- usuário com múltiplos vínculos setoriais

---

## 2.3 Servidor administrativo sem responsabilidade

### Perfil

Servidor técnico-administrativo comum, sem ser responsável de setor.

### Dados sugeridos

- `cpf`: `33333333333`
- `nome`: `Assistente Administrativo`
- perfil: `Servidor`
- cargo: `ASSISTENTE EM ADMINISTRACAO`
- vínculo com setor (no `SetorVinculo`):
  - setor: `DENS`
  - função: `MEMBRO`
  - responsavel: `False`

### Regra validada

- vínculo simples com setor
- função sem gratificação obrigatória

---

## 2.4 Aluno regular

### Perfil

Aluno com vínculo acadêmico, sem monitoria.

### Dados sugeridos

- `cpf`: `44444444444`
- `nome`: `Aluno Regular`
- perfil: `Aluno`
- curso: `Análise e Desenvolvimento de Sistemas`

### Regra validada

- aluno vinculado a curso sem obrigação organizacional

---

## 2.5 Aluno monitor

### Perfil

Aluno com vínculo acadêmico e atuação organizacional como monitor.

### Dados sugeridos

- `cpf`: `55555555555`
- `nome`: `Aluno Monitor`
- perfil: `Aluno`
- curso: `Licenciatura em Matemática`
- vínculo com setor (no `SetorVinculo`):
  - setor: `NAPNE/FLO`
  - função: `MONITOR`
  - responsavel: `False`

### Regra validada

- monitoria tratada como função
- aluno monitor vinculado a setor

---

## 2.6 Terceirizado

### Perfil

Usuário terceirizado vinculado a empresa.

### Dados sugeridos

- `cpf`: `66666666666`
- `nome`: `Terceirizado Limpeza`
- perfil: `Terceirizado`
- empresa: `EMPRESA LIMPEZA IFPI`
- setor opcional: `DENS`
- função opcional: `MEMBRO`

### Regra validada

- terceirizado com empresa
- separação entre cargo e terceirização

---

# 3. Cenários mínimos de seed

## Cenário 1 — Estrutura organizacional mínima

### Deve criar:

- setores
- funções
- cargos
- empresas
- cursos

### Objetivo

Garantir base de dados suficiente para criação dos perfis principais.

---

## Cenário 2 — Responsável de setor válido

### Deve criar:

- servidor
- cargo
- setor
- função de coordenação
- vínculo responsável

### Objetivo

Validar a regra:

- todo setor precisa de responsável
- responsável deve ser servidor

---

## Cenário 3 — Múltiplos vínculos para o mesmo usuário

### Deve criar:

- um servidor
- dois setores
- dois vínculos com funções diferentes

### Objetivo

Validar a possibilidade de múltiplos vínculos setoriais simultâneos.

---

## Cenário 4 — Aluno monitor

### Deve criar:

- usuário
- aluno
- curso
- função `MONITOR`
- vínculo com setor

### Objetivo

Validar que monitoria pertence ao domínio organizacional, não ao acadêmico.

---

## Cenário 5 — Terceirizado com empresa

### Deve criar:

- usuário
- terceirizado
- empresa

### Objetivo

Validar vínculo de terceirização.

---

# 4. Cenários de erro que devem ser testados

## 4.1 Criar vínculo com setor sem função

### Resultado esperado

Deve falhar.

### Regra validada

Todo `SetorVinculo` exige `Funcao`.

---

## 4.2 Definir aluno como responsável de setor

### Resultado esperado

Deve falhar.

### Regra validada

Responsável de setor deve ser servidor.

---

## 4.3 Definir terceirizado como responsável de setor

### Resultado esperado

Deve falhar.

### Regra validada

Responsável de setor deve ser servidor.

---

## 4.4 Criar servidor sem cargo

### Resultado esperado

Deve falhar.

### Regra validada

Todo `Servidor` deve possuir `Cargo`.

---

## 4.5 Criar terceirizado sem empresa

### Resultado esperado

Deve falhar.

### Regra validada

Todo `Terceirizado` deve possuir `EmpresaInstituicao`.

---

## 4.6 Criar usuário com CPF duplicado

### Resultado esperado

Deve falhar.

### Regra validada

CPF deve ser único.

---

## 4.7 Remover o único responsável de um setor sem substituição

### Resultado esperado

Deve falhar.

### Regra validada

Setor não pode ficar sem responsável válido.

---

# 5. Estratégia de seed recomendada

## Etapa 1 — catálogos

Criar primeiro:

- setores
- funções
- cargos
- empresas
- cursos

## Etapa 2 — usuários base

Criar os usuários com CPF e dados cadastrais mínimos.

## Etapa 3 — perfis

Criar:

- servidores
- alunos
- terceirizados

## Etapa 4 — vínculos

Criar:

- `AlunoCurso`
- `SetorVinculo`

---

# 6. Sugestão de organização futura do seed

Este documento não define ainda o formato técnico do seed, mas recomenda a separação por responsabilidade.

Exemplo futuro:

- seed de catálogos
- seed de usuários
- seed de perfis
- seed de vínculos

Isso pode ser feito depois por:

- comando customizado Django;
- fixtures;
- scripts Python internos;
- camada de business específica para carga inicial.

---

# 7. Critérios mínimos de validação manual

Após a seed inicial, deve ser possível confirmar manualmente:

- existe ao menos um setor com responsável válido;
- existe ao menos um usuário com múltiplos vínculos;
- existe ao menos um aluno monitor;
- existe ao menos um terceirizado com empresa;
- não existe setor com vínculo sem função;
- não existe servidor sem cargo;
- não existe terceirizado sem empresa.

---

# 8. Cenários que podem ser adicionados depois

Futuras expansões recomendadas:

- usuário com múltiplos perfis simultâneos
- mudança de responsável de setor
- desligamento de vínculo com setor
- histórico acadêmico com múltiplos cursos
- cenários com função gratificada
- cenários com setor inativo
- cenários com curso inativo

---

# Resumo executivo

A massa inicial do Cortex deve ser pequena, mas suficiente para validar as regras mais importantes do domínio.

Os cenários prioritários são:

- servidor responsável por setor;
- servidor com múltiplos vínculos;
- aluno regular;
- aluno monitor;
- terceirizado com empresa.

Esses cenários cobrem os pontos mais críticos da modelagem e ajudam a verificar se a implementação respeita corretamente os limites entre os domínios `Identidade`, `Organizacional`, `PessoasInstitucionais` e `Academico`.
