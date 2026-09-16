# Research: Modelo de Dados e Consultas

## Decisao: SQLite com SQLAlchemy 2.0 tipado

- **Decision**: Usar SQLite `vendas_b2b.db` e declarative mapping SQLAlchemy 2.0 com `Mapped` e `mapped_column`.
- **Rationale**: E a persistencia exigida pela constituicao, suficiente para o MVP local e reduz configuracao operacional em uma semana.
- **Alternatives considered**: PostgreSQL foi descartado por adicionar infraestrutura; SQL puro foi descartado por proibicao absoluta.

## Decisao: Repository por agregado consultado

- **Decision**: `ClienteRepository`, `PedidoRepository` e `FaturaRepository` concentram acesso ORM; services fazem calculos e composicao.
- **Rationale**: Mantem rotas e ferramentas sem dependencia direta de Models e torna as regras testaveis com sessoes substituiveis.
- **Alternatives considered**: Acesso direto nas rotas seria menor inicialmente, mas viola a constituicao e mistura transporte com persistencia.

## Decisao: Services de leitura com filtros limitados

- **Decision**: Expor consultas de credito, pedidos/entrega, faturas vencidas e risco; toda listagem tem limite e paginação.
- **Rationale**: Cobre os fluxos P1 da especificacao e evita consultas em massa acidentais.
- **Alternatives considered**: CRUD completo foi excluido do MVP por prazo e por não ser permitido pelo agente durante consultas.

## Decisao: Integridade em duas camadas

- **Decision**: Regras estruturais ficam em constraints/relacionamentos do modelo; regras dependentes de varias linhas ficam em services e testes de integração.
- **Rationale**: SQLite garante chaves e limites simples, enquanto total do pedido e consistencia cliente-pedido exigem contexto de aplicação.
- **Alternatives considered**: Triggers poderiam centralizar regras, mas aumentam complexidade e conflitam com a preferência por ORM simples e portável.

## Decisao: Contrato REST pequeno

- **Decision**: Rotas somente GET para `/clientes/{id}/credito`, `/clientes/{id}/pedidos`, `/pedidos/{id}`, `/clientes/{id}/faturas/vencidas` e `/clientes/{id}/risco`.
- **Rationale**: Mapeia diretamente as intenções do agente e permite validação rápida via Swagger/OpenAPI.
- **Alternatives considered**: Endpoint genérico de consulta foi evitado por dificultar autorização, paginação e controle de escopo.
