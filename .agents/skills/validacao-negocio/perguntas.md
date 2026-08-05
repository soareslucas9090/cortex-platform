# Exemplos de perguntas — skill validacao-negocio

## Atores e permissões

**Quem pode realizar esta ação?**
- A) Apenas o próprio usuário (dono do recurso)
- B) Gestor do setor / unidade (L2)
- C) Administrador global (L3)
- D) Qualquer pessoa autenticada
- Outro (descreva):

## Estados

**O registro pode existir em quais situações?**
- A) Ativo / Inativo (dois estados)
- B) Rascunho → Publicado → Arquivado
- C) Apenas criado ou excluído (sem estados intermediários)
- Outro (descreva):

## Duplicidade

**Pode existir mais de um registro igual?**
- A) Não — deve ser único (informar critério: CPF, e-mail, combinação X+Y)
- B) Sim — sem restrição
- C) Sim, mas apenas em contextos diferentes (ex.: setores distintos)
- Outro (descreva):

## Registro inativo

**O que acontece se o usuário tentar usar um vínculo/setor/conta inativo?**
- A) Bloquear com erro claro
- B) Permitir leitura, bloquear escrita
- C) Reativar automaticamente
- Outro (descreva):

## Concorrência

**Duas pessoas editam o mesmo registro ao mesmo tempo. O que deve prevalecer?**
- A) Última gravação ganha
- B) Primeira gravação bloqueia a segunda
- C) Mesclar campos não conflitantes
- D) Não se aplica / não sei
- Outro (descreva):

## Exclusão

**Como remover um registro deste fluxo?**
- A) Exclusão lógica (marca inativo, mantém histórico)
- B) Exclusão física (apaga do banco)
- C) Não pode ser removido — apenas encerrado
- Outro (descreva):
