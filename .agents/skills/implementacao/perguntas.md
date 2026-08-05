# Exemplos de perguntas — skill implementacao

Use como referência; adapte ao contexto. Sempre incluir **"Outro (descreva):"**.

## Domínio e escopo

**Qual domínio esta feature pertence?**
- A) Identidade (usuários, contas, autenticação)
- B) Organizacional (setores, vínculos)
- C) Pessoas Institucionais (servidores, alunos)
- D) Acadêmico (cursos, matrículas, turmas)
- Outro (descreva):

## Permissões

**Quem pode executar esta ação?**
- A) Qualquer usuário autenticado (L1)
- B) Gestor do setor / escopo limitado (L2)
- C) Administrador do sistema (L3)
- D) Endpoint público (sem login)
- Outro (descreva):

## Tipo de operação

**O que o endpoint deve fazer?**
- A) Criar um registro novo (POST)
- B) Listar registros com filtros (GET)
- C) Atualizar registro existente (PUT/PATCH)
- D) Remover ou desativar (DELETE)
- E) Mais de uma operação na mesma URL
- Outro (descreva):

## Regra de negócio ambígua

**O que acontece se [condição]?**
- A) Bloquear com mensagem de erro
- B) Permitir mas registrar aviso
- C) Ignorar silenciosamente
- Outro (descreva):

## App existente vs. novo

**Onde implementar?**
- A) Estender app existente: [nome sugerido após explorar código]
- B) Criar novo sub-app no domínio
- C) Não tenho certeza — recomende após analisar o código
- Outro (descreva):
