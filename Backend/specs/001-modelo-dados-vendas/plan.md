# Implementation Plan: Modelo de Dados e Consultas do Agente de Vendas B2B

**Branch**: `001-modelo-dados-vendas` | **Date**: 2026-08-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-modelo-dados-vendas/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Implementar o MVP de consultas comerciais sobre quatro tabelas relacionais, com separacao clara entre Models SQLAlchemy, Repositories, Services, Schemas Pydantic e Rotas FastAPI. O desenho privilegia uma unica aplicacao Python, SQLite local e consultas de leitura deterministicas, com uma semana para entregar o fluxo completo e testado.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.10+

**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2, Alembic, Uvicorn

**Storage**: SQLite `vendas_b2b.db`, com foreign keys habilitadas

**Testing**: Pytest, com testes unitarios de repositorios/servicos e integracao das rotas criticas

**Target Platform**: Servidor local ou container Linux/Windows executando a API REST

**Project Type**: Web service backend

**Performance Goals**: 95% das consultas de credito em ate 2 segundos; paginacao para listagens

**Constraints**: Uma semana de implementacao; sem SQL puro; acesso a dados somente por Repositories; agente somente leitura; tipagem completa; escopo restrito ao essencial

**Scale/Scope**: MVP para base local de clientes, pedidos e faturas; quatro tabelas de negocio e quatro consultas principais

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Resultado | Evidencia |
|---|---|---|
| Python 3.10+ e stack obrigatoria | PASS | Dependencias e linguagem seguem a constituicao. |
| SQLAlchemy 2.0 tipado e Alembic | PASS | Models usam `Mapped`/`mapped_column`; migracao inicial planejada. |
| Sem SQL puro | PASS | Repositories usarao `select()` e expressoes ORM; nenhum `execute("SELECT...")`. |
| Repository pattern | PASS | Rotas e services dependem de interfaces/repositorios, nao de Models diretamente. |
| Tipagem, PEP 8 e excecoes HTTP | PASS | Type hints em codigo novo, validacao Pydantic e mapeamento de erros nas rotas. |
| Leitura segura do agente | PASS | Endpoints/tooling nao terao mutacoes; simulacao de status fica em memoria. |
| Prazo de uma semana | PASS | Entrega fatiada em sete dias, com dados e consultas antes de refinamentos. |

## Project Structure

### Documentation (this feature)

```text
specs/001-modelo-dados-vendas/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
app/
├── api/
│   ├── dependencies.py
│   ├── errors.py
│   └── routes.py
├── db/
│   ├── base.py
│   └── session.py
├── models/
│   ├── cliente.py
│   ├── pedido.py
│   ├── item_pedido.py
│   └── fatura.py
├── repositories/
│   ├── cliente_repository.py
│   ├── pedido_repository.py
│   └── fatura_repository.py
├── schemas/
│   ├── cliente.py
│   ├── pedido.py
│   ├── fatura.py
│   └── consulta.py
├── services/
│   ├── credito_service.py
│   ├── pedido_service.py
│   └── risco_service.py
└── main.py

alembic/
├── versions/
└── env.py

tests/
├── integration/
│   └── test_rotas_consultas.py
└── unit/
    ├── test_repositories.py
    └── test_services.py
```

**Structure Decision**: Aplicacao backend unica com camadas explicitas. `models` define persistencia; `repositories` encapsulam consultas ORM; `services` calculam regras de credito/risco e consolidam dados; `schemas` definem entrada e saida; `api` valida contexto, converte excecoes e publica rotas. Os testes acompanham a mesma separacao.

## Technical Approach

1. **Bootstrap e persistencia**: configurar engine/sessao SQLite, habilitar foreign keys, criar Base declarativa e adicionar Alembic. A primeira migracao cria apenas as quatro tabelas de negocio e seus indices essenciais (`cnpj`, `numero_fatura`, chaves estrangeiras e datas de consulta).
2. **Models**: implementar os quatro modelos com `Mapped`, `mapped_column`, relacionamentos tipados, enums de status, constraints de valores e timestamps. Nao criar entidade de produto nem tabelas auxiliares no MVP.
3. **Repositories**: expor metodos de busca por identificador, resolucao ambigua de cliente, pedidos paginados, itens, faturas abertas/vencidas e agregados necessarios ao credito. Usar somente `select()`, joins e filtros ORM; cada metodo recebe a sessao e retorna entidades ou DTOs tipados.
4. **Services**: concentrar calculos de subtotal, saldo de fatura, exposicao, saldo disponivel, atraso e resumo de risco. Services nao recebem request HTTP nem instanciam Models; erros de dominio usam excecoes proprias.
5. **Schemas**: criar schemas Pydantic V2 para filtros, paginacao, cliente resolvido, credito, pedido detalhado, fatura vencida e risco. Validar limites, datas e enums antes de chamar os repositories.
6. **Rotas e agente**: publicar somente GET para os cinco recursos do contrato OpenAPI. Injetar sessao e repositories por dependencia; converter nao encontrado, ambiguidade e dados invalidos em respostas HTTP previsiveis. Tooling do agente deve delegar aos services e ter docstrings completas.
7. **Testes e aceite**: testar regras puras nos services, constraints e isolamento nos repositories, e cenarios completos nas rotas. Confirmar que chamadas de consulta nao executam mutacoes e que a migracao reproduz o schema.

## Sequenciamento de Uma Semana

| Dia | Entrega incremental | Saida verificavel |
|---|---|---|
| 1 | Bootstrap, dependencias, configuracao SQLite, Base e Alembic | Aplicacao inicia e migracao cria o banco vazio. |
| 2 | Quatro Models, relacionamentos, enums e constraints | Testes de integridade impedem dados invalidos e referencias orfas. |
| 3 | Repositories e fixtures de dados | Buscas por cliente/pedido/fatura funcionam com ORM tipado. |
| 4 | Services de credito, pedidos e faturas vencidas | Calculos derivados passam testes unitarios, inclusive bordas de data. |
| 5 | Schemas, dependencias e rotas GET | Swagger exibe o contrato e respostas HTTP sao consistentes. |
| 6 | Tool calls do agente e resumo de risco | Intencoes P1 delegam aos services; escrita e vazamento entre clientes sao bloqueados. |
| 7 | Integracao, desempenho basico, documentacao e correcao | Quickstart completo passa e MVP fica demonstravel. |

## Fora do Escopo do MVP

- CRUD de clientes, pedidos ou faturas exposto ao agente.
- Autenticacao/autorizacao completa, sincronizacao com ERP e fila de eventos.
- Cadastro de produtos, estoque, parcelas como entidade separada ou dashboards.
- Otimizacoes prematuras, cache distribuido e suporte a banco remoto.

## Reavaliacao Pos-Design

Todos os gates permanecem **PASS** após o design. A separacao de camadas atende ao Repository pattern; as consultas permanecem ORM-only; a leitura do agente e limitada a GET; e o escopo de sete dias evita funcionalidades fora do contrato. O unico ajuste de infraestrutura previsto e adicionar Alembic ao arquivo de dependencias durante a implementacao.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Nenhuma | N/A | A arquitetura proposta cumpre a constituicao sem excecoes. |
