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

## Phase 8: Frontend - Interface de chat (React, TypeScript, Vite e Tailwind)

**Purpose**: Criar a aplicacao web em `frontend/`, fora da pasta `Backend/`, e conecta-la ao fluxo de conversas persistidas e ao endpoint do agente.

**Goal**: Entregar uma interface basica e responsiva com sidebar de navegacao e uma area de chat funcional, permitindo iniciar uma conversa, selecionar conversas antigas e trocar mensagens com o agente.

**Independent Test**: Com o backend em execucao, abrir a aplicacao frontend, criar uma nova conversa, enviar uma mensagem, receber a resposta do agente, selecionar uma conversa existente na sidebar e confirmar que seu historico e carregado sem recarregar a pagina.

- [X] T056 Inicializar o projeto `frontend/` com Vite, React, TypeScript, Tailwind CSS e scripts de desenvolvimento, build e teste; manter configuracoes e dependencias isoladas do `Backend/`.
- [X] T057 Criar a camada de cliente HTTP tipada em `frontend/src/services/api.ts` para configurar a URL base do backend por variavel de ambiente e consumir `GET /api/v1/agent/conversations`, `GET /api/v1/agent/conversations/{conversation_id}` e `POST /api/v1/agent/chat`.
- [X] T058 Definir os tipos TypeScript de `ConversationSummary`, `ConversationHistory`, `ChatMessage`, `ChatRequest` e `ChatResponse`, alinhados aos schemas retornados pelo backend e sem duplicar regras de negocio no frontend.
- [X] T059 Implementar o layout principal em `frontend/src/App.tsx` com sidebar contendo o botao de nova conversa e a lista do historico, alem da area de chat com cabecalho, mensagens e compositor fixado na parte inferior.
- [X] T060 Implementar a selecao de conversas antigas na sidebar, carregando o historico pelo identificador e destacando a conversa ativa; ordenar e apresentar titulo, data ou estado de carregamento de forma legivel.
- [X] T061 Implementar o fluxo de nova conversa e envio de mensagem, preservando o `conversation_id` retornado pelo backend, adicionando mensagens do usuario a direita e respostas do agente a esquerda, com bloqueio de envio vazio ou duplicado durante a requisicao.
- [X] T062 Adicionar estados de carregamento, erro, lista vazia, resposta indisponivel e retry para carregamento do historico e envio de mensagens, sem expor detalhes internos do backend ao usuario.
- [X] T063 Garantir acessibilidade e responsividade basica: controles acionaveis por teclado, labels para input e botoes, foco apos envio, sidebar utilizavel em telas estreitas e mensagens sem overflow horizontal.
- [X] T064 Criar testes do frontend para renderizacao da sidebar, nova conversa, selecao de historico, envio com `conversation_id`, estados de erro e alinhamento visual das mensagens; mockar a API e nao depender de um LLM real.
- [ ] T065 Documentar em `frontend/README.md` a instalacao, variaveis de ambiente, comandos de desenvolvimento e build, URL esperada do backend, CORS necessario e fluxo manual de validacao ponta a ponta.

### Dependencies & Execution Order (Frontend)

- T056 bloqueia T057-T065 e deve ser concluida antes de qualquer implementacao de componente.
- T057-T058 podem ser executadas em paralelo; T059 depende da estrutura do projeto e dos tipos compartilhados.
- T060-T062 dependem da camada de API e do estado principal do chat; T063 pode ser executada em paralelo com T060-T062.
- T064 depende dos componentes e fluxos implementados; T065 deve registrar o comportamento validado apos o build.
- A validacao ponta a ponta depende de T053 e exige backend e frontend executando separadamente.

### Frontend Acceptance Criteria

- A aplicacao inicia a partir de `frontend/` com os scripts documentados e gera build de producao sem erros de TypeScript.
- A sidebar permite iniciar uma conversa e selecionar qualquer conversa retornada pelo backend.
- O chat envia apenas o texto e o identificador de conversa suportados pelo contrato, exibe a resposta retornada e preserva o historico selecionado.
- Mensagens do agente ficam alinhadas a esquerda e mensagens do usuario a direita, sem depender de texto codificado como regra de negocio.
- Falhas de rede, respostas 4xx/5xx e listas vazias possuem estados visiveis e recuperaveis.
- Nenhuma chave de provedor LLM ou credencial do backend e incluida no bundle do frontend.

## Phase 9: Convergence - Base de Conhecimento RAG com ChromaDB

**Purpose**: Implementar a consulta semantica das politicas B2B do playbook como uma nova capacidade somente leitura do agente, preservando a separacao entre ingestao, armazenamento vetorial, tool calling e orquestracao.

**Source of truth**: `docs/playbook_negociacao_b2b.md`, contendo as regras de alçada zero, retencao, cobranca, escalonamento e simulacao de Card Pipefy. O documento atualmente existente em `app/docs/playbook_negociacao_b2b.md` deve ser promovido ou sincronizado para o caminho canonico sem manter duas fontes divergentes.

**Traceability requirements**:

- **RAG-FR-001**: O sistema DEVE ingerir o playbook corporativo em Markdown e preservar o contexto dos cabecalhos nos fragmentos.
- **RAG-FR-002**: O sistema DEVE manter uma colecao ChromaDB persistida localmente, reutilizavel entre reinicios, com identificador estavel e metadados de origem.
- **RAG-FR-003**: O agente DEVE consultar a base semantica para perguntas sobre politicas B2B antes de formular orientacoes, sem inventar regras ausentes na KB.
- **RAG-FR-004**: A busca semantica DEVE ser exposta como tool LangChain com descricao, entrada tipada, limite de resultados e retorno serializavel.
- **RAG-FR-005**: A integracao RAG DEVE preservar o modo somente leitura, nao alterar dados comerciais e nao expor credenciais ou caminhos sensiveis.
- **RAG-SC-001**: A ingestao produz fragmentos nao vazios, identificados pela origem e pelo cabecalho Markdown correspondente.
- **RAG-SC-002**: Uma consulta sobre alçada zero, retencao ou escalonamento retorna trechos relevantes do playbook por meio da nova tool.
- **RAG-SC-003**: O chat do agente usa a nova tool em uma consulta de politica e continua respondendo com o contrato atual de `POST /api/v1/agent/chat`.

- [X] T066 [P] Consolidar a fonte de verdade em `docs/playbook_negociacao_b2b.md`, migrando ou sincronizando `app/docs/playbook_negociacao_b2b.md` sem duplicar conteudo divergente, e documentar no proprio arquivo a versao/origem usada pela ingestao (RAG-FR-001, RAG-SC-001, missing)
- [X] T067 [P] Adicionar `chromadb`, `langchain-text-splitters` e `langchain-core` em `requirements.txt`, fixando versoes compativeis com Python 3.10 e documentando a instalacao no quickstart (RAG-FR-002, RAG-FR-004, plan: dependencias, missing)
- [X] T068 Implementar `app/services/chromadb_service.py` com leitura UTF-8 do Markdown, `MarkdownTextSplitter` configurado para preservar cabecalhos, metadados de origem/secao, colecao estavel e persistencia local configuravel fora do codigo-fonte (RAG-FR-001, RAG-FR-002, Constituição II, missing)
- [X] T069 Implementar no `ChromaDBService` a ingestao idempotente do playbook, evitando duplicacao de documentos em execucoes repetidas, validando fragmentos vazios e permitindo recriacao controlada da colecao sem alterar dados do dominio (RAG-FR-001, RAG-FR-002, RAG-FR-005, missing)
- [X] T070 [P] Criar testes unitarios em `app/tests/unit/test_chromadb_service.py` cobrindo leitura por cabecalhos, metadados de secao, fragmentos nao vazios, persistencia configurada, ingestao idempotente e isolamento com uma colecao/cliente Chroma de teste (RAG-SC-001, RAG-FR-002, Constituição V, missing)
- [X] T071 Implementar funcao de similaridade em `app/services/chromadb_service.py` e expo-la como `@tool` LangChain em `app/agent/tools.py`, com consulta obrigatoria, `top_k` limitado, retorno de conteudo/metadados/distancias e erro explicito quando a KB nao estiver disponivel (RAG-FR-003, RAG-FR-004, Constituição IV, missing)
- [X] T072 Atualizar `app/agent/prompts.py` e `app/agent/service.py` para registrar a tool de busca semantica no fluxo de tool calling e orientar o agente a consultar o playbook para alçada, retencao, negociacao, descontos, parcelamento e escalonamento, distinguindo politica recuperada de dado transacional (RAG-FR-003, RAG-FR-005, partial)
- [X] T073 [P] Criar testes de integracao em `app/tests/integration/test_agent_chat.py` para uma consulta de politica com cliente LLM mockado, verificando chamada da tool RAG, retorno de trecho relevante, continuidade do historico, tratamento de KB indisponivel e ausencia de mutacao no banco (RAG-SC-002, RAG-SC-003, RAG-FR-005, missing)
- [X] T074 Atualizar `app/tests/conftest.py`, configuracao e documentacao de execucao para isolar o diretorio/colecao Chroma nos testes, impedir dependencia de rede ou credenciais externas e incluir comando de ingestao inicial no quickstart (RAG-FR-002, RAG-SC-001, Constituição V, missing)
- [X] T075 Executar a validacao final da feature com `pytest`, instalacao limpa das dependencias, ingestao repetida, consulta semantica e `POST /api/v1/agent/chat`, registrando no quickstart o criterio de aceite e qualquer limitacao de modelo de embedding (RAG-SC-001, RAG-SC-002, RAG-SC-003, missing)

### Dependencies & Execution Order (RAG)

- T066 e T067 podem ser preparados em paralelo; T068 depende de T066 e T067.
- T069 depende de T068 e bloqueia T070, T071 e T074.
- T070 pode ser executada em paralelo com T071 apos T069.
- T071 depende de T068-T069 e bloqueia T072.
- T072 depende de T071 e da infraestrutura existente de T050/T049; T073 depende de T072.
- T074 pode ser executada em paralelo com T072-T073, mas deve estar concluida antes de T075.
- T075 depende de T066-T074 e e o aceite integrado da nova capacidade RAG.

### RAG Acceptance Criteria

- A ingestao usa exclusivamente `docs/playbook_negociacao_b2b.md` como fonte canonica e conserva o cabecalho de cada fragmento nos metadados.
- A colecao ChromaDB permanece disponivel apos reiniciar o processo e uma segunda ingestao nao duplica os fragmentos.
- A tool LangChain aceita uma pergunta em linguagem natural e retorna os trechos mais similares com origem e secao identificaveis.
- O agente consulta a KB para regras de negociacao e declara quando uma resposta depende de politica recuperada, sem usar a busca semantica para substituir as tools transacionais.
- Testes unitarios e de integracao executam sem rede, sem chave de LLM real, sem credenciais Chroma externas e sem mutar clientes, pedidos ou faturas.

## Constitutional Gates

- SQLAlchemy 2.0 tipado com `Mapped`/`mapped_column` e Alembic.
- Nenhuma string de SQL puro; toda persistencia passa por repositories ORM.
- Rotas e tools nao instanciam Models diretamente.
- Type hints completos, PEP 8, Pydantic V2 e erros de negocio mapeados para HTTP.
- Agente em modo de leitura; nenhuma criacao, atualizacao, exclusao, liquidacao ou cancelamento durante consultas.
- Testes Pytest cobrem repositories, services, rotas criticas, integridade e nao mutacao.
