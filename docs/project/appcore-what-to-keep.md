# AppCore — O que manter sem grandes mudanças

## Objetivo

Este documento registra os componentes do `AppCore` e da base atual que podem ser mantidos sem necessidade de reformulação estrutural imediata.

A ideia é preservar aquilo que já está alinhado ao Cortex, evitando retrabalho desnecessário.

---

## 1. Arquitetura em camadas

### Manter

A separação entre:

- `business.py`
- `rules.py`
- `helpers.py`
- `state.py`

### Motivo

Essa arquitetura já está coerente com a forma como o Cortex está sendo documentado e planejado.

Ela ajuda a:

- manter views leves;
- evitar lógica concentrada nas rotas;
- separar validação, orquestração e utilidades.

---

## 2. Mixins de acesso às camadas

### Manter

- `ModelBusinessMixin`
- `ModelHelperMixin`
- `ModelRulesMixin`
- `ModelStateMixin`

### Motivo

Esses mixins oferecem um padrão de acesso limpo e coerente para os models do domínio.

Exemplos:

- `obj.business.metodo()`
- `obj.helper.metodo()`
- `obj.rules.metodo()`
- `obj.state.metodo()`

---

## 3. Views base

### Manter

- `BasicPostAPIView`
- `BasicGetAPIView`
- `BasicRetrieveAPIView`
- `BasicPutAPIView`
- `BasicPatchAPIView`
- `BasicDeleteAPIView`

### Motivo

As views base já fornecem:

- padronização de fluxo;
- integração com serializer;
- transação em operações de escrita;
- tratamento centralizado de exceções;
- respostas uniformes.

### Observação

Elas podem receber pequenos ajustes finos depois, mas sua estrutura principal pode ser mantida.

---

## 4. Exceções customizadas

### Manter

- `BusinessRuleException`
- `ValidationException`
- `AuthorizationException`
- `NotFoundException`
- `SystemErrorException`

### Motivo

Essas exceções criam uma base clara para o tratamento padronizado das falhas de domínio e sistema.

---

## 5. Permissões base

### Manter

- `AllowAnyPermission`
- `IsOwnerOrAdminPermission`
- `IsAdminPermission`

### Motivo

A estratégia está simples, objetiva e suficiente para a fase atual do Cortex.

### Observação

No futuro, novas permissões podem ser adicionadas, mas não há necessidade de repensar essas imediatamente.

---

## 6. Paginação customizada

### Manter

`PaginacaoCustomizada`

### Motivo

A implementação atual é simples, clara e útil para o padrão de API desejado.

Ela já resolve:

- tamanho padrão;
- ajuste por query param;
- limite mínimo e máximo.

---

## 7. Separação entre `AppCore`, `Auth` e `Cortex`

### Manter

A estrutura conceitual com:

- `AppCore/`
- `Auth/`
- `Cortex/`

### Motivo

Essa divisão continua fazendo sentido:

- `AppCore` como base reutilizável;
- `Auth` como thin app de autenticação;
- `Cortex` como projeto/configuração.

---

## 8. Modelo base de usuário genérico

### Manter conceitualmente

`AbstractBaseAppUser`

### Motivo

Como base genérica, ele continua útil.

### Observação importante

Ele não deve ser descartado, mas o projeto precisa criar um model concreto alinhado ao Cortex.

Ou seja:

- a abstração pode permanecer;
- a concretização no domínio do projeto ainda precisa ser resolvida.

---

## Resumo executivo

A base atual não precisa ser reconstruída.  
Os principais componentes estruturais do `AppCore` podem ser preservados, especialmente:

- arquitetura em camadas;
- mixins;
- views base;
- exceções;
- permissões;
- paginação;
- separação entre base, auth e projeto.

A estratégia recomendada é **manter a fundação e ajustar os pontos críticos**, em vez de recomeçar.
