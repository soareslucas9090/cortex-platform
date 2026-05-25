---
description: "Regras do domínio PessoasInstitucionais do projeto Cortex."
applyTo: "PessoasInstitucionais/**"
---

# PessoasInstitucionais

Use estas regras junto com [docs/antigravity/project-rules.md](../../docs/antigravity/project-rules.md), [docs/antigravity/rules/pessoas-institucionais.md](../../docs/antigravity/rules/pessoas-institucionais.md) e os dados de seeds em [docs/seeds/documentação DER - cortex.md](../../docs/seeds/documentação DER - cortex.md).

- Os dados de seeds para os models `Cargo` e `EmpresaInstituicao` devem ser importados a partir de [docs/seeds/documentação DER - cortex.md](../../docs/seeds/documentação DER - cortex.md).
- `Servidor` e `Terceirizado` devem usar `OneToOneField` com `primary_key=True` para herança física de `Usuario`.
- `Servidor` depende de `Cargo`.
- `Terceirizado` depende de `EmpresaInstituicao`.
- As choices de jornada do servidor são `20`, `40` e `0`.
- Mantenha os apps internos separados por responsabilidade: `cargos`, `servidores`, `empresas_instituicoes` e `terceirizados`.
