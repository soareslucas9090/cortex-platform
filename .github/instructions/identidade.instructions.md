---
description: "Regras do domínio Identidade do projeto Cortex."
applyTo: "Identidade/**"
---

# Identidade

Use estas regras junto com [docs/antigravity/project-rules.md](docs/antigravity/project-rules.md) e [docs/antigravity/rules/identidade.md](docs/antigravity/rules/identidade.md).

- O login é por `cpf`, nunca por e-mail.
- Não existe auto-cadastro; usuários são criados por administradores via endpoint específico ou pelo portal Admin.
- A criação de usuários deve suportar payload individual ou em lote via JSON.
- `Usuario` é a base central do domínio e se relaciona com `Contato`, `Endereco` e `Matricula`.
- Mantenha a estrutura do domínio sob `Identidade/` com apps internos separados por model principal.
