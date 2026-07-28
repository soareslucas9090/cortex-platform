# Diretrizes do Domínio: Organizacional

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Organizacional** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Organizacional` gerencia a estrutura administrativa do projeto, como setores, funções e os vínculos dos usuários a essas estruturas.

### Modelos e Relacionamentos

- **Setor**: Unidade administrativa ou departamento dentro da instituição. Os dados raízes/seeds para os setores encontram-se em [docs/seeds/documentação DER - cortex.md](../seeds/documentação DER - cortex.md).
- **Funcao**: Atividade ou cargo de confiança desempenhado por um usuário no setor. Os dados raízes/seeds para as funções encontram-se em [docs/seeds/documentação DER - cortex.md](../seeds/documentação DER - cortex.md).
- **SetorVinculo**: Tabela associativa (M:N) que vincula um `Usuario` a um `Setor` com uma determinada `Funcao`.

### Estrutura de Apps

```text
Organizacional/
├── __init__.py
├── urls.py
├── setores/         # App Django do model Setor
├── funcoes/         # App Django do model Funcao
└── vinculos/        # App Django do model SetorVinculo
```

---

## Regras Específicas do Domínio

### 1. Setor e Vínculos
- A relação entre um usuário e um setor é representada pelo model `SetorVinculo`.
- A função ou papel desempenhado (incluindo monitorias) deve ser explicitada pelo relacionamento FK com `Funcao`, e não através de flags booleanas no modelo de usuário ou do setor.
- O campo `responsavel` indica se o usuário é o responsável principal pelo setor.

#### Modelagem de `SetorVinculo`
```python
class SetorVinculo(ModelHelperMixin, ModelBusinessMixin, BasicModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, ...)
    setor = models.ForeignKey('setores.Setor', on_delete=models.CASCADE, ...)
    funcao = models.ForeignKey('funcoes.Funcao', on_delete=models.PROTECT, ...)
    responsavel = models.BooleanField('Responsável', default=False)
```
