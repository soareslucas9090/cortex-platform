# Plano da Milestone 5 — Integração e Consolidação Final

## Objetivo

A Milestone 5 existe para consolidar a integração final do Cortex, após a implementação dos domínios centrais do sistema.

Essa etapa deve garantir que os domínios já implementados funcionem de forma coerente entre si, respeitando as fronteiras de responsabilidade, as regras interdomínio e a arquitetura estrutural do projeto.

Ao final desta milestone, o projeto deve estar estruturalmente consistente, funcionalmente coerente e documentalmente alinhado.

---

## Domínios envolvidos

Esta milestone atua sobre a integração entre os seguintes domínios já implementados:

- `Identidade`
- `Organizacional`
- `PessoasInstitucionais`
- `Academico`

---

## Resultado esperado ao final da milestone

Ao final da Milestone 5, o sistema deve estar apto a:

1. operar com coerência entre identidade, perfis institucionais, perfis acadêmicos e vínculos organizacionais;
2. refletir corretamente as invariantes que dependem de mais de um domínio;
3. manter separação conceitual entre contextos de negócio;
4. expor rotas e estruturas compatíveis com a arquitetura final do projeto;
5. possuir documentação principal coerente com a implementação real.

---

## Escopo da milestone

Esta milestone pode incluir:

- ajustes de integração entre domínios;
- ajustes pontuais em models, business, rules, helpers, serializers, views, urls e testes, quando estritamente necessários para consolidar a integração final;
- revisão de coerência estrutural do projeto;
- revisão de exposição das rotas agregadas;
- revisão da documentação principal;
- validação funcional mínima do sistema.

---

## O que não entra

Esta milestone **não deve** incluir:

- criação de novos domínios;
- criação arbitrária de novos apps fora de necessidade real identificada;
- refactor amplo sem justificativa;
- mudança de arquitetura do projeto;
- absorção indevida de responsabilidades de um domínio por outro;
- reintrodução do modelo antigo de um app único por domínio.

---

## Decisões já consolidadas que esta milestone deve respeitar

1. O sistema é organizado por domínio.
2. Os domínios são módulos agregadores, não apps únicos.
3. Os apps internos devem ser finos e, em regra, cada app corresponde a um model principal.
4. O projeto segue arquitetura em camadas.
5. Views devem permanecer leves.
6. `Cargo` e `Funcao` são conceitos diferentes.
7. Monitoria pertence ao domínio `Organizacional`.
8. `Aluno` depende da identidade do usuário.
9. `Servidor` e `Terceirizado` dependem da identidade do usuário.
10. O sistema deve preservar separação entre identidade, perfil institucional, perfil acadêmico e vínculo organizacional.

---

## Progresso

| Etapa | Status |
|-------|--------|
| 5.1 | Concluída (14/07/2026) |
| 5.2 | Concluída |
| 5.3 | Concluída |
| 5.4 | Concluída |
| 5.5 | Concluída (14/07/2026) |
| 5.6 | Parcial |

---

## Frentes internas da milestone

## Etapa 5.1 — Integração `Identidade` + `PessoasInstitucionais`

### Objetivo
Consolidar a relação entre a identidade do usuário e os perfis institucionais formais.

### Inclui
- revisão da relação entre `Usuario`, `Servidor` e `Terceirizado`;
- validação das dependências corretas;
- ajustes mínimos necessários em camadas e testes.

### Critério de saída
A identidade e os perfis institucionais devem estar integrados de forma coerente, sem sobreposição indevida de responsabilidades.

### Status
Concluída (14/07/2026) — exposição de `servidor` e `terceirizado` em `UsuarioSerializer` via reverse relations; queryset `queryset_usuario_com_perfis()` para listagem/detalhe; testes em `Identidade/usuarios/tests/test_perfil_institucional.py`.

---

## Etapa 5.2 — Integração `Identidade` + `Academico`

### Objetivo
Consolidar a relação entre a identidade do usuário e o perfil acadêmico.

### Inclui
- revisão da relação entre `Usuario`, `Aluno` e `AlunoCurso`;
- validação das dependências corretas;
- ajustes mínimos necessários em camadas e testes.

### Critério de saída
A identidade e o domínio acadêmico devem estar integrados de forma coerente, sem acoplamento indevido.

---

## Etapa 5.3 — Integração `Organizacional` + `PessoasInstitucionais`

### Objetivo
Consolidar regras organizacionais que dependem de perfil institucional formal.

### Inclui
- revisão da elegibilidade institucional do responsável de setor;
- revisão da relação entre vínculos organizacionais e perfis institucionais;
- ajustes mínimos necessários em camadas e testes.

### Critério de saída
As regras organizacionais dependentes de perfil institucional devem estar refletidas corretamente na implementação.

---

## Etapa 5.4 — Integração `Organizacional` + `Academico`

### Objetivo
Garantir que as relações entre domínio organizacional e acadêmico permaneçam corretas e sem duplicação de responsabilidade.

### Inclui
- validação da decisão de que monitoria pertence ao domínio organizacional;
- revisão de possíveis dependências entre `Aluno` e vínculos organizacionais;
- ajustes mínimos necessários em camadas e testes.

### Critério de saída
A fronteira entre acadêmico e organizacional deve permanecer clara e sem duplicação de regras.

---

## Etapa 5.5 — Revisão estrutural e documental final

### Objetivo
Consolidar a coerência estrutural e documental do projeto.

### Inclui
- revisão de `Cortex/settings.py`;
- revisão de `Cortex/urls.py`;
- revisão dos `urls.py` agregadores de domínio;
- revisão dos apps registrados;
- revisão da documentação principal;
- atualização dos artefatos principais do projeto quando necessário.

### Critério de saída
A estrutura do projeto e a documentação principal devem refletir corretamente a implementação final.

### Status
Concluída (14/07/2026) — `settings.py` e `urls.py` revisados; apps e rotas agregadas validados; `django-project-tree.md`, `README.md`, checklist global, plano mestre e `copilot-instructions.md` alinhados com a estrutura real (incluindo domínio `Infraestrutura`).

---

## Etapa 5.6 — Validação funcional mínima do sistema

### Objetivo
Executar uma validação funcional mínima dos principais fluxos e vínculos do sistema.

### Inclui
- revisão dos cenários mínimos já definidos;
- validação dos fluxos essenciais do sistema;
- consolidação dos testes mínimos necessários.

### Critério de saída
O projeto deve demonstrar coerência mínima de ponta a ponta para os cenários centrais já definidos.

---

## Critérios de aceite da milestone

A Milestone 5 só deve ser considerada concluída quando:

### 1. As integrações interdomínio estiverem consolidadas
- `Identidade` + `PessoasInstitucionais`
- `Identidade` + `Academico`
- `Organizacional` + `PessoasInstitucionais`
- `Organizacional` + `Academico`

### 2. As invariantes cruzadas estiverem refletidas
- sem contradições entre domínios;
- sem duplicação de responsabilidade.

### 3. A estrutura do projeto estiver coerente
- apps registrados corretamente;
- rotas agregadas corretamente;
- módulos de domínio bem definidos.

### 4. A documentação principal estiver alinhada
- instruções do repositório;
- árvore do projeto;
- checklist global;
- plano mestre.

### 5. A validação funcional mínima estiver concluída
- com testes e cenários mínimos compatíveis com o estágio do projeto.

---

## Riscos da milestone

## 1. Duplicar regras entre domínios
Isso pode tornar o sistema inconsistente.

## 2. Quebrar fronteiras conceituais
Especialmente entre identidade, institucional, acadêmico e organizacional.

## 3. Expandir escopo além da consolidação
Esta milestone deve fechar o sistema, não abrir novos blocos arbitrariamente.

## 4. Tratar documentação como secundária
Nesta etapa, a coerência documental é parte do resultado final.

---

## Arquivos impactados prioritariamente

Espera-se impacto principalmente em:

- domínios já implementados;
- `Cortex/settings.py`
- `Cortex/urls.py`
- urls agregadas de domínio
- testes
- documentação principal do projeto

---

## Saídas esperadas

Ao final da milestone, espera-se ter:

- integração coerente entre os domínios;
- invariantes cruzadas refletidas no código;
- rotas e apps organizados de forma consistente;
- documentação principal atualizada;
- validação funcional mínima concluída.

---

## Próximo passo após esta milestone

Após a conclusão e revisão da Milestone 5, o próximo passo não deve ser uma nova milestone estrutural imediata, mas sim:

- manutenção evolutiva;
- refinamentos;
- novas demandas de domínio, caso surjam.

---

## Resumo executivo

A Milestone 5 consolida a integração final do Cortex.

Ela existe para fechar o sistema de forma coerente, garantindo integração entre os domínios já implementados, preservando fronteiras conceituais e alinhando a documentação principal com a implementação real.