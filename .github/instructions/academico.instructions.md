---
description: "Regras do domínio Acadêmico do projeto Cortex."
applyTo: "Academico/**"
---

# Acadêmico

Use estas regras junto com [docs/antigravity/project-rules.md](docs/antigravity/project-rules.md) e [docs/antigravity/rules/academico.md](docs/antigravity/rules/academico.md).

- `Aluno` deve usar `OneToOneField` com `primary_key=True` para herança física de `Usuario`.
- As choices de situação do aluno são `MATRICULADO`, `TRANCADO`, `FORMADO`, `DESISTENTE` e `TRANSFERIDO`.
- As choices de turno são `MATUTINO`, `VESPERTINO`, `NOTURNO` e `INTEGRAL`.
- As choices de forma de ingresso são `VESTIBULAR`, `ENEM`, `TRANSFERENCIA` e `REINGRESSO`.
- Mantenha os apps internos separados por responsabilidade: `alunos`, `cursos` e `aluno_cursos`.
