# Plano de Alteração do AppCore — Arquivo por Arquivo

## Objetivo

Este documento descreve, arquivo por arquivo, as alterações recomendadas na base atual do projeto antes do início efetivo dos apps de domínio do Cortex.

O foco principal desta rodada é:

1. resolver a autenticação por email ou CPF;
2. remover o filtro automático de `ativo=True` do `BaseManager`;
3. alinhar o thin app `Auth` à estratégia real do projeto;
4. reduzir inconsistências estruturais já identificadas na revisão do AppCore.

---

# Bloco 1 — Autenticação email/CPF

## 1. `Cortex/settings.py`

### Alterações recomendadas

- ajustar `AUTH_USER_MODEL` para o model concreto futuro do domínio `identidade`
- adicionar `AUTHENTICATION_BACKENDS`
- revisar documentação/comentários do settings para refletir a nova estratégia

### Objetivo

Garantir que a configuração central do Django reflita a autenticação real do Cortex.

### Estado desejado

- `AUTH_USER_MODEL` apontando para o usuário concreto do projeto
- `AUTHENTICATION_BACKENDS` incluindo backend customizado por email/CPF

### Observação

Enquanto o app `identidade` ainda não existir, essa alteração pode ser preparada conceitualmente e aplicada quando o model concreto for criado.

---

## 2. `AppCore/basics/auth/backends.py`

### Situação

Arquivo ainda não existe.

### Alteração recomendada

Criar este arquivo.

### Responsabilidade do novo arquivo

Implementar o backend customizado de autenticação por email ou CPF.

### Classe sugerida

- `EmailOrCpfBackend`

### Responsabilidades da classe

- receber `login` ou `username`;
- detectar email ou CPF;
- normalizar valor;
- buscar usuário pelo model configurado;
- validar senha;
- respeitar `user_can_authenticate(user)`.

### Objetivo

Centralizar a lógica de autenticação no lugar correto: backend de autenticação do Django.

---

## 3. `AppCore/common/util/util.py`

### Alterações recomendadas

- adicionar uma função de normalização de CPF
- revisar utilitários relacionados a autenticação, se necessário
- revisar `enviar_email_simples` para evitar exposição de erro interno

### Função sugerida

- `normalizar_cpf(valor)`

### Responsabilidade

Receber CPF com ou sem máscara e retornar apenas dígitos.

### Objetivo

Reutilizar normalização em autenticação, managers e validações.

---

## 4. `Auth/auth/serializers.py`

### Alterações recomendadas

Substituir o contrato atual de autenticação por um contrato explícito com:

- `login`
- `password`

### Ajustes específicos

- alterar `LoginSerializer` para autenticar com identificador híbrido;
- deixar de depender da suposição de login apenas por email;
- ajustar `LoginInputSerializer` para documentar `login` como email ou CPF;
- revisar `LoginResponseSerializer` se necessário.

### Objetivo

Alinhar o thin app `Auth` ao comportamento real desejado para o Cortex.

---

## 5. `Auth/auth/views.py`

### Alterações recomendadas

- manter a estrutura de `LoginView`
- revisar `extend_schema` para refletir corretamente o novo contrato de login
- garantir que a view esteja usando o serializer concreto correto

### Objetivo

Fazer a view documentar e expor corretamente o fluxo por email/CPF sem recriar desnecessariamente a lógica de autenticação.

---

## 6. `AppCore/basics/auth/serializers.py`

### Alterações recomendadas

Revisar se os serializers base continuam genéricos o suficiente e, ao mesmo tempo, não atrapalham o uso do login híbrido.

### Possíveis ajustes

- permitir uso mais claro de um campo genérico de login;
- evitar documentação ou expectativa excessivamente centrada em email;
- manter o AppCore genérico, mas menos enviesado.

### Objetivo

Garantir que a base de autenticação não conflite com a implementação concreta do Cortex.

---

## 7. `AppCore/basics/auth/views.py`

### Alterações recomendadas

- revisar exemplos Swagger que ainda assumem email como padrão;
- tornar a documentação base menos enviesada para email;
- manter a view base simples e reutilizável.

### Objetivo

Evitar inconsistência documental entre base genérica e projeto real.

---

## 8. `AppCore/basics/models/user_model.py`

### Alterações recomendadas

- manter o model abstrato como base genérica;
- revisar documentação interna para reconhecer melhor o caso de login híbrido;
- revisar exemplos para não ficarem excessivamente presos a um único identificador.

### Objetivo

Preservar a reutilização do AppCore, mas com uma base documental mais aderente ao tipo de projeto que o Cortex se tornou.

---

# Bloco 2 — Remoção do filtro implícito de ativos

## 9. `AppCore/basics/models/models.py`

### Alterações recomendadas

- remover o override de `filter()` que injeta `ativo=True`;
- manter `get()` com tratamento de `NotFoundException`, se continuar fazendo sentido;
- deixar o manager base com comportamento previsível.

### Objetivo

Eliminar efeito colateral invisível nas consultas.

### Estado desejado

- `filter()` volta a se comportar como no Django;
- o conceito de “ativos” deixa de ser automático.

---

## 10. Helpers futuros dos domínios

### Arquivos futuros impactados

- `identidade/helpers.py`
- `organizacional/helpers.py`
- `pessoas_institucionais/helpers.py`
- `academico/helpers.py`

### Direção recomendada

Criar consultas explícitas como:

- `obter_usuarios_ativos()`
- `obter_setores_ativos()`
- `obter_funcoes_ativas()`
- `obter_servidores_ativos()`
- `obter_cursos_ativos()`

### Objetivo

Transferir a semântica de ativos para camadas explícitas e orientadas ao domínio.

---

# Bloco 3 — Ajustes de coerência e segurança

## 11. `AppCore/common/util/util.py`

### Alterações recomendadas

Além da normalização de CPF:

- revisar `enviar_email_simples`;
- substituir mensagens com detalhe técnico por mensagens genéricas;
- usar logging interno.

### Objetivo

Aderir às diretrizes de segurança já documentadas no projeto.

---

## 12. `AppCore/basics/decorators/decorators.py`

### Alterações recomendadas

- revisar consistência de imports;
- revisar estilo e formatação;
- verificar se as mensagens usadas continuam coerentes com o padrão atual do projeto.

### Objetivo

Manter a boa ideia do decorator, mas com base mais limpa.

---

## 13. `AppCore/basics/views/basic_views.py`

### Alterações recomendadas

- simplificar trechos com `raise e` para `raise`;
- revisar pequenos detalhes de clareza e legibilidade;
- manter a estrutura central das views base.

### Objetivo

Limpeza técnica sem alteração estrutural grande.

---

## 14. `Auth/auth/serializers.py` e `Auth/auth/views.py`

### Alterações adicionais

Além da autenticação híbrida:

- revisar exemplos Swagger;
- alinhar mensagens e descrições;
- garantir que o contrato do login fique completamente explícito.

### Objetivo

Evitar que a documentação da API continue contradizendo o comportamento real.

---

# Bloco 4 — Arquivos futuros diretamente impactados pela decisão

## 15. `identidade/models.py`

### Situação

Arquivo futuro.

### Alteração planejada

Implementar o model concreto `Usuario`.

### Responsabilidades esperadas

- herdar da base adequada;
- possuir `email` único;
- possuir `cpf` único;
- normalizar email e CPF;
- definir manager concreto;
- integrar corretamente com autenticação do sistema.

### Objetivo

Fechar definitivamente o elo entre domínio `Identidade` e autenticação do projeto.

---

## 16. `identidade/helpers.py`

### Situação

Arquivo futuro.

### Alteração planejada

Criar consultas explícitas de ativos e de busca por identificadores relevantes.

### Objetivo

Absorver a semântica de consulta que não deve ficar mais no manager base.

---

## 17. `identidade/business.py`

### Situação

Arquivo futuro.

### Alteração planejada

Centralizar regras de criação e manutenção do usuário concreto.

### Objetivo

Evitar espalhar lógica de normalização, validação e criação em serializers ou views.

---

# Ordem recomendada de execução das alterações

## Etapa 1 — preparar autenticação

1. criar backend customizado
2. definir utilitário de normalização de CPF
3. ajustar serializers do `Auth`
4. ajustar view/documentação do login
5. preparar `settings.py`

## Etapa 2 — limpar manager base

6. remover filtro implícito de ativos do `BaseManager`

## Etapa 3 — corrigir coerência e segurança

7. revisar utilitários com vazamento de erro
8. revisar views base
9. revisar documentação base do auth

## Etapa 4 — conectar com o domínio real

10. implementar `identidade.Usuario`
11. configurar `AUTH_USER_MODEL`
12. consolidar login real do projeto

---

# Itens que podem esperar um pouco

Os itens abaixo não bloqueiam imediatamente o início da revisão estrutural, mas devem entrar em sequência:

- refinamento de exemplos Swagger genéricos;
- revisão estética de comentários e textos;
- padronização fina de aspas e mensagens;
- aprofundamento do módulo de login social.

---

# Resumo executivo

As alterações mais importantes, arquivo por arquivo, concentram-se em:

- `Cortex/settings.py`
- `AppCore/basics/auth/backends.py` (novo)
- `AppCore/common/util/util.py`
- `Auth/auth/serializers.py`
- `Auth/auth/views.py`
- `AppCore/basics/models/models.py`

Esses arquivos formam o núcleo da rodada inicial de refatoração que deve ocorrer antes da implementação efetiva dos apps de domínio do Cortex.
