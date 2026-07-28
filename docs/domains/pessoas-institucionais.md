# Diretrizes do Domínio: Pessoas Institucionais

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Pessoas Institucionais** do projeto Cortex.

## Visão Geral do Domínio

O domínio `PessoasInstitucionais` gerencia os diferentes tipos de colaboradores da instituição, como servidores públicos e funcionários terceirizados, bem como cargos e empresas parceiras.

### Modelos e Relacionamentos

- **Cargo**: Cargos públicos ou posições estruturadas na instituição. Os dados raízes/seeds para os cargos encontram-se em [docs/seeds/documentação DER - cortex.md](../seeds/documentação DER - cortex.md).
- **Servidor**: Colaborador efetivo ou comissionado. Possui relação de herança 1:1 com `Usuario` e depende de um `Cargo`.
- **EmpresaInstituicao**: Empresas parceiras ou prestadoras de serviço à instituição. Os dados raízes/seeds para as empresas/instituições encontram-se em [docs/seeds/documentação DER - cortex.md](../seeds/documentação DER - cortex.md).
- **Terceirizado**: Colaborador contratado por intermédio de uma empresa parceira. Possui relação de herança 1:1 com `Usuario` e depende de `EmpresaInstituicao`.
- **Estagiario**: Colaborador em regime de estágio (planejado na hierarquia de herança).

### Estrutura de Apps

```text
PessoasInstitucionais/
├── __init__.py
├── urls.py
├── cargos/                  # App Django do model Cargo
├── servidores/              # App Django do model Servidor
├── empresas_instituicoes/   # App Django do model EmpresaInstituicao
└── terceirizados/           # App Django do model Terceirizado
```

---

## Regras Específicas do Domínio

### 1. Herança de Usuários para Servidores e Terceirizados
- Usamos **OneToOneField com primary_key=True** para herança física de models estendendo `Usuario`.
- Isso evita herança de tabelas do Django (multi-table inheritance nativa) que gera performance ruim em queries complexas.

#### Modelagem de `Servidor`
```python
class Servidor(BasicModel):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='servidor',
        primary_key=True,
    )
    # campos específicos do servidor...
```

### 2. Choices e Parâmetros
- **Jornada de Trabalho Servidor**:
  - `20` (20 horas semanais)
  - `40` (40 horas semanais)
  - `0` (Dedicação Exclusiva)
