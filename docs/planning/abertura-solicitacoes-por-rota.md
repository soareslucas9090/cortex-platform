# Abertura das solicitações por rota

## Pedido e decisão de negócio

Permitir ao administrador definir a abertura das solicitações no cadastro da rota.
O usuário confirmou que a escolha entre mesmo dia e dia anterior cabe ao administrador.

## Plano de implementação

1. Adicionar `horario_abertura_solicitacoes` à Rota e ao histórico; derivar o dia da abertura pela comparação com o horário de saída.
2. Validar em Rules a abertura até o limite de 30 minutos antes da saída; Business orquestra criação e edição.
3. Expor os campos em serializers de criação, edição e consulta e no Django Admin, mantendo views leves e escrita L3.
4. Aplicar a configuração às reservas, entrada/saída da fila, cancelamento, listagem para alunos e geração pelo Celery.
5. Atualizar a documentação de domínio, Swagger e documentação viva das permissões.
6. Verificar migração, API, limites temporais, permissões e regressões do Transporte.

## Contrato

- `horario_abertura_solicitacoes`: `HH:MM` ou `HH:MM:SS`; resposta `HH:MM:SS`.
- Fuso: America/Fortaleza; abertura e limite final inclusivos.
- Compatibilidade: valores omitidos na criação usam 19:00; o dia é derivado pela comparação com o horário de saída.
- No PATCH, campos ausentes são preservados e a combinação completa é revalidada.
- Configuração consultada na rota: editar afeta execuções abertas existentes, preservando tickets.
- A capacidade e a saída da execução continuam congeladas; o encerramento continua relativo à saída da execução.
- Calendário operacional, elegibilidade, permissões e bloqueios continuam aplicáveis.
- O Beat mantém a frequência de cinco minutos, criando cada execução no primeiro processamento elegível.

## Versionamento e validação

Branch: `feat/horario-abertura-solicitacoes-por-rota`.
Commits no padrão Conventional Commits, em português, sem escopo e sem ponto final.

Testes: cadastro/edição/leitura, API/Admin, entradas inválidas, L3 versus aluno,
virada de dia, segundos, abertura exata e T-30, geração idempotente por rota,
filtros de disponibilidade, preservação de tickets e migração de registros antigos.
