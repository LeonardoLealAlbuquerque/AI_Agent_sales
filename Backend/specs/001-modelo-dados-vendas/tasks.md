# Tasks: Modelo de Dados e Consultas do Agente de Vendas B2B

**Input**: Design documents from `/specs/001-modelo-dados-vendas/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Strategy**: Implementar primeiro a fundacao, entregar US1 como MVP, adicionar US2 e US3 incrementalmente e finalizar com integracao, documentacao e desempenho. Todas as consultas do agente sao somente leitura.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar a aplicacao Python, banco e ferramentas de teste.

- [X] T001 [P] Criar a estrutura de pacotes `app/api`, `app/db`, `app/models`, `app/repositories`, `app/schemas` e `tests`
- [X] T002 [P] Atualizar dependencias em `requirements.txt` com Alembic, pytest, pytest-asyncio e httpx
- [X] T003 [P] Configurar `app/core/config.py` com SQLite `vendas_b2b.db` e configuracao substituivel em testes
- [X] T004 [P] Criar `tests/conftest.py` com banco SQLite em memoria, sessoes isoladas e fixtures das quatro entidades
- [X] T005 [P] Configurar `app/db/session.py` com engine, sessoes tipadas e foreign keys SQLite habilitadas
- [X] T006 [P] Criar `app/db/base.py` com `DeclarativeBase` e registro dos modelos
- [X] T007 Configurar `alembic.ini` e `alembic/env.py` para usar a metadata dos modelos
- [X] T008 Criar `app/main.py` com aplicacao FastAPI e endpoint inicial de health check
- [X] T009 Executar o bootstrap e confirmar que `pytest -q` e a aplicacao inicial executam sem erro em `tests/`

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implementar persistencia, integridade e contratos compartilhados antes das historias.

- [X] T010 [P] Implementar o modelo `Cliente` em `app/models/cliente.py` com `Mapped`, CNPJ unico, limite e status
- [X] T011 [P] Implementar o modelo `Pedido` em `app/models/pedido.py` com cliente obrigatorio, status e entrega
- [X] T012 [P] Implementar o modelo `ItemPedido` em `app/models/item_pedido.py` com quantidade, desconto e subtotal
- [X] T013 [P] Implementar o modelo `Fatura` em `app/models/fatura.py` com vencimento, pagamento e pedido opcional
- [X] T014 Consolidar enums, relacionamentos tipados e exportacoes em `app/models/__init__.py`
- [X] T015 Adicionar constraints, indices e regras de exclusao nos modelos em `app/models/`
- [X] T016 Implementar validacoes transacionais de total do pedido e consistencia fatura-pedido-cliente em `app/services/validation_service.py`
- [X] T017 Criar a migracao inicial com exatamente `Clientes`, `Pedidos`, `Itens_Pedido` e `Faturas` em `alembic/versions/initial_schema.py`
- [X] T018 [P] Criar schemas compartilhados de identificacao, filtros, paginacao e data de referencia em `app/schemas/consulta.py`
- [X] T019 [P] Criar excecoes de dominio e mapeamento de erros HTTP em `app/api/errors.py`
- [X] T020 Criar interfaces base de repositories e injecao de sessao somente leitura em `app/repositories/base.py` e `app/api/dependencies.py`

**Checkpoint**: A fundacao esta pronta quando a migracao cria quatro tabelas, as constraints passam e nenhuma rota acessa Models diretamente.

## Phase 3: User Story 1 - Consultar credito de um cliente (Priority: P1) MVP

**Goal**: Retornar limite, exposicao, saldo disponivel, status e data de referencia sem alterar dados.

**Independent Test**: Cliente identificado com faturas abertas retorna valores corretos; cliente ambiguo, inexistente ou inelegivel nao expoe dados.

- [X] T021 [US1] Implementar `ClienteRepository` para busca por ID, CNPJ e nome parcial com desambiguacao em `app/repositories/cliente_repository.py`
- [X] T022 [US1] Implementar `FaturaRepository` para exposicao e saldo de faturas nao canceladas em `app/repositories/fatura_repository.py`
- [X] T023 [US1] Implementar calculo de credito, bloqueio e origem dos totais em `app/services/credito_service.py`
- [X] T024 [P] [US1] Criar schemas de resposta de credito e cliente em `app/schemas/cliente.py` e `app/schemas/consulta.py`
- [X] T025 [US1] Implementar `GET /clientes/{id_cliente}/credito` em `app/api/routes/credito.py`
- [X] T026 [P] [US1] Criar testes unitarios de credito, exposicao, limite zero, cliente inativo e bloqueado em `tests/unit/test_credito_service.py`
- [X] T027 [P] [US1] Criar testes do repository para identificacao, ambiguidade e isolamento em `tests/unit/test_cliente_repository.py`
- [X] T028 [US1] Criar testes de integracao da rota, 404/409/422 e nao mutacao em `tests/integration/test_credito_route.py`

## Phase 4: User Story 2 - Acompanhar pedidos e entrega (Priority: P1)

**Goal**: Consultar pedidos, itens, status, total e informacoes de entrega.

**Independent Test**: Pedido existente retorna status, itens, total e previsao ou entrega real; cancelados e entregues sao classificados corretamente.

- [X] T029 [US2] Implementar consultas paginadas de pedidos por cliente, status e periodo em `app/repositories/pedido_repository.py`
- [X] T030 [US2] Implementar consulta de itens e detalhe do pedido em `app/repositories/pedido_repository.py`
- [X] T031 [US2] Implementar total, previsao, entrega real e atraso em `app/services/pedido_service.py`
- [X] T032 [US2] Criar schemas de pedido, item, entrega e paginacao em `app/schemas/pedido.py`
- [X] T033 [US2] Implementar rotas GET de listagem e detalhe em `app/api/routes/pedidos.py`
- [X] T034 [P] [US2] Criar testes unitarios de subtotal, total, transicoes e classificacao de entrega em `tests/unit/test_pedido_service.py`
- [X] T035 [US2] Criar testes de repository e rotas para filtros, paginação, inexistencia e isolamento em `tests/integration/test_pedidos.py`

## Phase 5: User Story 3 - Consultar faturas vencidas e risco (Priority: P1)

**Goal**: Listar faturas vencidas e consolidar indicadores de risco por cliente e periodo.

**Independent Test**: Somente faturas elegiveis aparecem com saldo e dias de atraso; o risco nao mistura clientes.

- [X] T036 [US3] Implementar consulta paginada de faturas vencidas e agregados por periodo em `app/repositories/fatura_repository.py`
- [X] T037 [US3] Implementar saldo, dias de atraso e estados derivados em `app/services/fatura_service.py`
- [X] T038 [US3] Implementar consolidacao de exposicao, maior atraso e pedidos abertos em `app/services/risco_service.py`
- [X] T039 [P] [US3] Criar schemas de fatura vencida, risco e inconsistencias em `app/schemas/fatura.py` e `app/schemas/risco.py`
- [X] T040 [US3] Implementar rotas GET de faturas vencidas e resumo de risco em `app/api/routes/faturas.py` e `app/api/routes/risco.py`
- [X] T041 [P] [US3] Criar testes de vencimento hoje, atraso, pagamento, cancelamento e inconsistencias em `tests/unit/test_fatura_service.py`
- [X] T042 [US3] Criar testes de integracao de faturas, risco, filtros, 404/422, isolamento e bloqueio de mutacoes em `tests/integration/test_faturas_risco.py`

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Integrar o MVP, validar contrato e deixar a execucao reproduzivel.

- [X] T043 [P] Implementar tools de consulta do agente com docstrings completas e delegacao aos services em `app/api/tools.py`
- [X] T044 [P] Completar o contrato OpenAPI com cinco endpoints GET, schemas, filtros, paginacao e erros em `specs/001-modelo-dados-vendas/contracts/openapi.yaml`
- [X] T045 Criar seed demonstrativo, atualizar quickstart e executar migracao, pytest, smoke test, desempenho e checklist em `scripts/seed_demo.py`, `specs/001-modelo-dados-vendas/quickstart.md` e `specs/001-modelo-dados-vendas/checklists/requirements.md`

## Dependencies & Execution Order

- Setup (T001-T009) nao depende de outras fases.
- Foundational (T010-T020) depende do Setup e bloqueia todas as user stories.
- US1 (T021-T028) e US2 (T029-T035) podem avancar em paralelo apos Foundational.
- US3 (T036-T042) depende dos repositories e services compartilhados; pode iniciar apos T022, T031 e T037, com integracao final apos US1/US2.
- Polish (T043-T045) depende das rotas e testes das historias.
- Dentro de cada historia: testes de unidade podem ser preparados em paralelo; services dependem de repositories; rotas dependem de services; integracao valida o incremento completo.

## Parallel Opportunities

- T001-T006 podem ser executadas em paralelo.
- T010-T013 podem ser executadas em paralelo apos T006.
- T018-T020 podem ser executadas em paralelo apos os tipos basicos.
- T021 e T022 podem ser executadas em paralelo; T026 e T027 tambem.
- T029, T032 e T034 podem ser paralelizadas quando os modelos estiverem prontos.
- T039 e T041 podem ser paralelizadas com a preparacao das rotas de US3.
- T043 e T044 podem ser executadas em paralelo; T045 e a validacao final.

## Implementation Strategy

1. Concluir Setup e Foundational; validar migracao, quatro tabelas e integridade.
2. Entregar US1 como MVP demonstravel e validar independentemente.
3. Adicionar US2 sem quebrar US1; validar pedidos, itens e entrega.
4. Adicionar US3 com vencimento e risco; validar isolamento e datas-limite.
5. Integrar tools, contrato, seed, quickstart e medicao final.

## Phase 7: Convergence

**Purpose**: Avancar para o Spec 002, implementando a orquestracao do Agente de IA sobre as tools de consulta ja entregues em `app/api/tools.py`, sem criar uma segunda camada de acesso a dados.

- [X] T046 [P] Configurar o cliente LLM e suas variaveis de ambiente em `requirements.txt`, `app/core/config.py` e `.env.example`, incluindo provedor compatível, modelo, chave, URL opcional, timeout e limites de tokens; falhar com erro de configuracao acionavel quando a chave for exigida e nao estiver presente (Spec 002/configuracao, missing)
- [X] T047 Criar uma abstracao injetavel de cliente LLM em `app/agent/llm_client.py`, com implementacao real e double de teste, sem chamadas de rede durante os testes e com tratamento de timeout, indisponibilidade e resposta invalida (Spec 002/configuracao, missing)
- [X] T048 Definir o System Prompt versionado da Persona do Agente B2B em `app/agent/prompts.py`, orientando linguagem profissional, escopo de consultas comerciais, coleta de filtros minimos, desambiguacao de clientes, transparencia sobre data/origem dos dados e bloqueio de qualquer operacao de escrita (Spec 002/persona, missing)
- [ ] T049 Mapear as funcoes existentes de `app/api/tools.py` para schemas de function calling/tool binding em `app/agent/tools.py`, preservando `get_client_risk_analysis`, `get_client_credit_limit`, `get_overdue_invoices`, `get_client_orders` e `get_order_details` como unica implementacao; declarar argumentos, descricoes, limites e retorno serializavel (FR-010, Constituição IV, partial)
- [X] T050 Implementar o orquestrador do agente em `app/agent/service.py`, compondo prompt, historico da conversa, cliente LLM e registry de tools; executar chamadas de ferramenta com argumentos validados, devolver o resultado ao modelo, limitar iteracoes, rejeitar tool desconhecida e nunca expor credenciais ou permitir mutacoes (Spec 002/orquestracao, missing)
- [X] T051 Criar schemas Pydantic para entrada e saida do chat em `app/schemas/agent.py`, cobrindo mensagem obrigatoria, historico opcional, identificador de conversa se suportado, resposta textual, ferramentas acionadas e erros publicaveis sem dados sensiveis (Spec 002/contrato de chat, missing)
- [X] T052 Implementar `POST /api/v1/agent/chat` em `app/api/routes/agent.py`, injetando o orquestrador, validando o request, retornando resposta deterministica para sucesso, ambiguidade e nao encontrado e mapeando falhas do LLM para HTTP sem vazar excecoes internas (Spec 002/endpoint, missing)
- [X] T053 Registrar a rota do agente em `app/api/router.py` e integrar configuracao, dependencias e observabilidade minima do fluxo sem alterar as rotas GET existentes ou permitir acesso direto do LLM aos Models (Constituição III-IV, missing)
- [X] T054 [P] Criar testes de integracao em `app/tests/integration/test_agent_chat.py` com cliente LLM mockado, cobrindo resposta direta, chamada e retorno de cada tool existente, multiplas iteracoes, argumento invalido, tool desconhecida, timeout/erro do provedor, pedido ambiguo, tentativa de escrita e ausencia de mutacao no banco (Spec 002/aceite, missing)
- [ ] T055 Atualizar `specs/001-modelo-dados-vendas/quickstart.md` com instalacao do SDK, `.env.example`, configuracao segura da chave, inicializacao do servidor e exemplos de `POST /api/v1/agent/chat`; documentar que os testes usam mock e que as tools operam somente em leitura (T045, missing)

### Dependencies & Execution Order (Spec 002)

- T046 bloqueia T047 e T050; T048 e T049 podem ser preparados em paralelo apos a definicao do contrato do agente.
- T047 depende de T046 e bloqueia T050 e T054.
- T050 depende de T047-T049 e bloqueia T052.
- T051 pode ser executada em paralelo com T048-T050; T052 depende de T050-T051; T053 depende de T052.
- T054 depende de T049-T053; T055 pode ser atualizado em paralelo com T054 e deve registrar o fluxo validado.

## Constitutional Gates

- SQLAlchemy 2.0 tipado com `Mapped`/`mapped_column` e Alembic.
- Nenhuma string de SQL puro; toda persistencia passa por repositories ORM.
- Rotas e tools nao instanciam Models diretamente.
- Type hints completos, PEP 8, Pydantic V2 e erros de negocio mapeados para HTTP.
- Agente em modo de leitura; nenhuma criacao, atualizacao, exclusao, liquidacao ou cancelamento durante consultas.
- Testes Pytest cobrem repositories, services, rotas criticas, integridade e nao mutacao.
