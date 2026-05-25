---
description: "Regras do domínio Organizacional do projeto Cortex."
applyTo: "Organizacional/**"
---

# Organizacional

Use estas regras junto com [docs/antigravity/project-rules.md](../../docs/antigravity/project-rules.md), [docs/antigravity/rules/organizacional.md](../../docs/antigravity/rules/organizacional.md) e os dados de seeds em [docs/seeds/documentação DER - cortex.md](../../docs/seeds/documentação DER - cortex.md).

- Os dados de seeds para os models `Setor` e `Funcao` devem ser importados a partir de [docs/seeds/documentação DER - cortex.md](../../docs/seeds/documentação DER - cortex.md).
- `SetorVinculo` representa o vínculo entre `Usuario` e `Setor`.
- A função desempenhada no setor deve ser representada por FK para `Funcao`, nunca por flags booleanas em outros models.
- O campo `responsavel` indica a responsabilidade principal pelo setor.
- Mantenha `setores`, `funcoes` e `vinculos` como apps internos separados do domínio.
