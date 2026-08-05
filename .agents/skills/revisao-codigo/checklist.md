# Checklist resumido — revisao-codigo

Detalhes e exemplos: `docs/project/guia-revisao-de-codigo.md`

## Views
- [ ] Herda de exatamente uma `Basic*APIView` do AppCore
- [ ] Sem ORM, sem `transaction`, sem lógica de negócio
- [ ] Hooks `do_action_*` delegam ao Business
- [ ] `@extend_schema` com bloco **Permissões** (L1/L2/L3 ou Público)
- [ ] Múltiplos verbos HTTP → `roteador_por_metodo` com views separadas

## Business
- [ ] Todo método com `try/except` envolvendo o corpo inteiro
- [ ] Catch-all usa `relancar_ou_erro_sistema` — sem expor `str(e)` ao cliente
- [ ] Orquestra Rules, Helpers, State — não chamados pela view

## Rules
- [ ] Métodos em português: `pode_*`, `validar_*`, `verificar_*`
- [ ] Sem persistência (`.save()`, `.create()`, `.delete()`)
- [ ] Retorna `True` ou lança exceção — não `False` silencioso

## Helpers
- [ ] Apenas queries e utilitários
- [ ] Chamado pelo Business, não pela view

## Models
- [ ] Herda `BasicModel` / mixins corretos do AppCore
- [ ] App no módulo de domínio correto

## Serializers
- [ ] Validação de formato no serializer; regra de negócio nas Rules
- [ ] Campos coerentes com o domínio (`docs/domains/`)

## URLs
- [ ] Todo `path()` tem `name=`
- [ ] Testes usam `reverse()`, não paths hardcoded

## Testes
- [ ] Cobrem cenário feliz e erros principais
- [ ] Permissões testadas quando aplicável
