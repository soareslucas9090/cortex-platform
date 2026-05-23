---
description: "Regras do domínio PessoasInstitucionais do projeto Cortex."
applyTo: "PessoasInstitucionais/**"
---

# PessoasInstitucionais

Use estas regras junto com [docs/antigravity/project-rules.md](docs/antigravity/project-rules.md) e [docs/antigravity/rules/pessoas-institucionais.md](docs/antigravity/rules/pessoas-institucionais.md).

- `Servidor` e `Terceirizado` devem usar `OneToOneField` com `primary_key=True` para herança física de `Usuario`.
- `Servidor` depende de `Cargo`.
- `Terceirizado` depende de `EmpresaInstituicao`.
- As choices de jornada do servidor são `20`, `40` e `0`.
- Mantenha os apps internos separados por responsabilidade: `cargos`, `servidores`, `empresas_instituicoes` e `terceirizados`.
