# Diretrizes do Domínio: Acadêmico

Este arquivo contém as regras, modelos e convenções específicas para o domínio **Acadêmico** do projeto Cortex.

## Visão Geral do Domínio

O domínio `Academico` gerencia a estrutura educacional do projeto, abrangendo alunos, cursos e matrículas em cursos.

### Modelos e Relacionamentos

- **Aluno**: Discente da instituição. Possui relação de herança 1:1 com `Usuario`.
- **Curso**: Cursos ofertados pela instituição. Os dados raízes/seeds para os cursos encontram-se em [docs/seeds/documentação DER - cortex.md](../seeds/documentação DER - cortex.md).
- **AlunoCurso**: Tabela de associação (M:N) ligando um `Aluno` a um `Curso`.

### Estrutura de Apps

```text
Academico/
├── __init__.py
├── urls.py
├── alunos/          # App Django do model Aluno
├── cursos/          # App Django do model Curso
└── aluno_cursos/    # App Django do model AlunoCurso (se aplicável)
```

---

## Regras Específicas do Domínio

### 1. Herança do Model `Aluno`
- Assim como nos outros perfis institucionais, a herança com `Usuario` deve ser implementada com **OneToOneField com primary_key=True**.

#### Modelagem de `Aluno`
```python
class Aluno(BasicModel):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name='aluno',
        primary_key=True,
    )
    # campos específicos do aluno...
```

### 2. Choices e Parâmetros Acadêmicos
- **Situação do Aluno**:
  - `MATRICULADO`
  - `TRANCADO`
  - `FORMADO`
  - `DESISTENTE`
  - `TRANSFERIDO`
- **Forma de Ingresso**:
  - `VESTIBULAR`
  - `ENEM`
  - `TRANSFERENCIA`
  - `REINGRESSO`
