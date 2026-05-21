# Checklist Global de Implementação do Cortex

## Objetivo

Este documento acompanha a implementação do Cortex em nível macro, organizando o progresso por milestone e por apps internos de cada domínio.

Ele deve funcionar como checklist vivo do projeto, servindo para:

- acompanhar o que já foi implementado e validado;
- orientar a ordem de execução;
- registrar a evolução estrutural do sistema;
- evitar perda de contexto durante refactors e mudanças arquiteturais.

---

## Princípios deste checklist

1. O projeto é organizado por **domínios**, e cada domínio pode conter múltiplos apps.
2. Em regra, cada **app corresponde a um model principal**.
3. Exceções só devem existir quando houver justificativa clara, como:
   - tabelas de domínio;
   - tabelas auxiliares;
   - M:N sem lógica própria relevante;
   - casos explicitamente decididos.
4. Milestones continuam sendo orientadas por domínio.
5. A execução interna de cada milestone deve respeitar a granularidade real dos apps do projeto.
6. Um item só deve ser marcado quando estiver **implementado e validado**.

---

# Milestone 0 — Fundação técnica

## Base do projeto

- [x] Revisar `AppCore`
- [x] Revisar `Auth`
- [x] Revisar `Cortex`
- [x] Validar arquitetura em camadas
- [x] Consolidar padrão de views leves com BasicViews
- [x] Ajustar autenticação para email/CPF
- [x] Ajustar `AUTH_USER_MODEL` para o model real do projeto
- [x] Remover comportamento implícito inadequado do manager base
- [x] Consolidar convenções de nomenclatura em português
- [x] Definir módulos de domínio como agregadores estruturais
- [x] Milestone validada

---

# Milestone 1 — Domínio Identidade

## Estrutura do domínio

- [x] Criar módulo `Identidade/`
- [x] Criar `Identidade/urls.py`

## App `usuarios`

- [x] Criar app `Identidade/usuarios/`
- [x] Implementar model `Usuario`
- [x] Implementar manager de usuário
- [x] Integrar `AUTH_USER_MODEL`
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls
- [x] Validar integração com autenticação

## App `contatos`

- [x] Criar app `Identidade/contatos/`
- [x] Implementar model `Contato`
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls

## App `enderecos`

- [x] Criar app `Identidade/enderecos/`
- [x] Implementar model `Endereco`
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls

## App `matriculas`

- [x] Criar app `Identidade/matriculas/`
- [x] Implementar model `Matricula`
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls

## Integração interna do domínio

- [x] Integrar os apps do domínio `Identidade`
- [x] Validar rotas do módulo `Identidade`
- [x] Validar consistência estrutural do domínio
- [x] Milestone validada

---

# Milestone 2 — Domínio Organizacional

## Estrutura do domínio

- [x] Criar módulo `Organizacional/`
- [x] Criar `Organizacional/urls.py`

## App `setores`

- [x] Criar app `Organizacional/setores/`
- [x] Implementar model `Setor`
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls

## App `funcoes`

- [x] Criar app `Organizacional/funcoes/`
- [x] Implementar model `Funcao`
- [x] Implementar atributo `e_gratificada`
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls

## App `vinculos`

- [x] Criar app `Organizacional/vinculos/`
- [x] Implementar model `SetorVinculo`
- [x] Garantir função obrigatória no vínculo
- [x] Modelar monitoria como função
- [x] Implementar camadas do app
- [x] Implementar serializers, views e urls

## Integração interna do domínio

- [x] Integrar os apps do domínio `Organizacional`
- [x] Validar rotas do módulo `Organizacional`
- [ ] Consolidar regra completa de responsável de setor
- [x] Validar consistência estrutural do domínio
- [ ] Milestone validada

> Observação: a validação completa da elegibilidade institucional do responsável depende da Milestone 3.

---

# Milestone 3 — Domínio PessoasInstitucionais

## Estrutura do domínio

- [ ] Criar módulo `PessoasInstitucionais/`
- [ ] Criar `PessoasInstitucionais/urls.py`

## App `servidores`

- [ ] Criar app `PessoasInstitucionais/servidores/`
- [ ] Implementar model `Servidor`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## App `cargos`

- [ ] Criar app `PessoasInstitucionais/cargos/`
- [ ] Implementar model `Cargo`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## App `terceirizados`

- [ ] Criar app `PessoasInstitucionais/terceirizados/`
- [ ] Implementar model `Terceirizado`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## App `empresas_instituicoes`

- [ ] Criar app `PessoasInstitucionais/empresas_instituicoes/`
- [ ] Implementar model `EmpresaInstituicao`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## Integração interna do domínio

- [ ] Integrar os apps do domínio `PessoasInstitucionais`
- [ ] Consolidar regra de responsável de setor ser servidor
- [ ] Validar consistência estrutural do domínio
- [ ] Milestone validada

---

# Milestone 4 — Domínio Acadêmico

## Estrutura do domínio

- [ ] Criar módulo `Academico/`
- [ ] Criar `Academico/urls.py`

## App `alunos`

- [ ] Criar app `Academico/alunos/`
- [ ] Implementar model `Aluno`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## App `cursos`

- [ ] Criar app `Academico/cursos/`
- [ ] Implementar model `Curso`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## App `aluno_cursos`

- [ ] Criar app `Academico/aluno_cursos/`
- [ ] Implementar model `AlunoCurso`
- [ ] Implementar camadas do app
- [ ] Implementar serializers, views e urls

## Integração interna do domínio

- [ ] Integrar os apps do domínio `Academico`
- [ ] Validar consistência estrutural do domínio
- [ ] Milestone validada

---

# Milestone 5 — Integração e consolidação final

## Integração entre domínios

- [ ] Integrar `Identidade` com `PessoasInstitucionais`
- [ ] Integrar `Identidade` com `Academico`
- [ ] Integrar `Organizacional` com `PessoasInstitucionais`
- [ ] Integrar `Organizacional` com `Academico`
- [ ] Consolidar invariantes cruzadas

## Validação estrutural

- [ ] Revisar `INSTALLED_APPS`
- [ ] Revisar `AUTH_USER_MODEL`
- [ ] Revisar agregadores `urls.py` dos domínios
- [ ] Revisar coerência das BasicViews
- [ ] Revisar documentação Swagger
- [ ] Revisar consistência dos nomes em português

## Documentação final

- [ ] Atualizar `docs/project/django-project-tree.md`
- [ ] Atualizar `docs/project/implementation-checklist.md`
- [ ] Atualizar ADRs e diagramas impactados
- [ ] Atualizar `.github/copilot-instructions.md`

## Validação final

- [ ] Executar cenários mínimos de uso
- [ ] Validar autenticação
- [ ] Validar integrações principais
- [ ] Milestone validada

---

# Observações finais

- Este checklist deve permanecer no projeto enquanto a implementação estiver evoluindo.
- Planos de milestone e prompts operacionais podem ser descartados após a conclusão e validação de cada etapa, mas este documento deve ser preservado.
- Em caso de refactor estrutural relevante, este arquivo deve ser atualizado antes da continuidade da implementação.
