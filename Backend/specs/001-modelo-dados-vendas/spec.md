# Feature Specification: Modelo de Dados e Consultas do Agente de Vendas B2B

**Feature Branch**: `001-modelo-dados-vendas`

**Created**: 2026-08-22

**Status**: Draft

**Input**: User description: "/specify Crie o documento de especificação detalhando o banco de dados com as 4 tabelas relacionais do Agente de Vendas B2B (Clientes, Pedidos, Itens_Pedido e Faturas) e as regras de consulta para o agente, respeitando rigorosamente a constituição."

## User Scenarios & Testing

### User Story 1 - Consultar crédito de um cliente (Priority: P1)

Como membro da equipe de vendas, quero consultar o limite, o comprometimento e o saldo de crédito de um cliente para decidir se uma nova negociação pode prosseguir.

**Why this priority**: A consulta de crédito é essencial para reduzir risco comercial e é um dos objetivos centrais do agente.

**Independent Test**: Com um cliente que possua limite e faturas em aberto, consultar o cliente por CNPJ ou identificador e verificar que o agente retorna os valores calculados e a data de referência, sem alterar dados.

**Acceptance Scenarios**:

1. **Given** um cliente identificado de forma única e com limite de crédito cadastrado, **When** o usuário pergunta pelo crédito disponível, **Then** o agente retorna limite, exposição em aberto, saldo disponível e indicador de bloqueio.
2. **Given** mais de um cliente compatível com o termo informado, **When** o usuário solicita a consulta, **Then** o agente pede um identificador adicional e não escolhe um cliente arbitrariamente.
3. **Given** um cliente inexistente ou inativo, **When** o usuário solicita a consulta, **Then** o agente informa que não encontrou um cliente elegível e não expõe registros de outro cliente.

### User Story 2 - Acompanhar pedidos e entrega (Priority: P1)

Como membro da equipe de vendas, quero saber o status de um pedido e a previsão de entrega para responder rapidamente ao cliente.

**Why this priority**: O acompanhamento de pedidos é uma necessidade operacional frequente e depende diretamente da relação entre cliente, pedido e itens.

**Independent Test**: Consultar um pedido existente por identificador, com itens e status de entrega, e conferir que a resposta contém o status atual, a previsão e os dados resumidos do pedido.

**Acceptance Scenarios**:

1. **Given** um pedido existente associado a um cliente, **When** o usuário pergunta pelo seu status, **Then** o agente retorna status, data do pedido, previsão de entrega, entrega efetiva quando houver e total.
2. **Given** um pedido entregue, **When** o usuário pergunta pela entrega, **Then** o agente informa a data de entrega efetiva e não apresenta a previsão como se fosse a data real.
3. **Given** um pedido cancelado, **When** o usuário pergunta pela entrega, **Then** o agente informa que não haverá entrega e preserva o registro histórico.

### User Story 3 - Consultar faturas vencidas e risco (Priority: P1)

Como membro da equipe de vendas, quero identificar faturas em atraso e receber um resumo de risco por cliente ou período.

**Why this priority**: A inadimplência deve ser identificada antes de novas ações comerciais e é explicitamente parte do domínio do agente.

**Independent Test**: Consultar um cliente com faturas abertas e vencidas e verificar que somente faturas elegíveis são listadas, com dias de atraso, valor em aberto e total consolidado.

**Acceptance Scenarios**:

1. **Given** uma fatura não paga cuja data de vencimento já passou, **When** o usuário pergunta por faturas vencidas, **Then** o agente lista a fatura, o vencimento, os dias de atraso e o saldo em aberto.
2. **Given** uma fatura paga ou cancelada, **When** o usuário pergunta por faturas vencidas, **Then** a fatura não é classificada como vencida.
3. **Given** um pedido de análise de risco sem cliente nem intervalo definidos, **When** o usuário solicita o relatório, **Then** o agente pede os filtros mínimos antes de consultar dados em massa.

### Edge Cases

- Cliente com limite de crédito nulo, negativo ou ausente não pode ser considerado apto; o dado deve ser rejeitado ou sinalizado como inconsistente.
- Pedido sem itens, item com quantidade não positiva ou preço negativo deve ser rejeitado por integridade de negócio.
- Fatura com valor pago maior que o valor total, vencimento anterior à emissão ou pagamento sem status compatível deve ser sinalizada como inconsistente.
- Fatura em aberto com vencimento igual ao dia corrente não é vencida; atraso começa no dia seguinte.
- Pedidos e faturas inexistentes devem produzir resposta de não encontrado, sem erro genérico ou inferência do agente.
- Dados de clientes diferentes não podem ser misturados em totais, listas ou relatórios.
- Consultas sem limite de período ou paginação devem usar limites operacionais definidos pelo serviço e informar quando houver truncamento.
- Alterações, exclusões e pagamentos não podem ser executados pelo agente durante consultas.

## Requirements

### Modelo relacional

O banco de dados deve conter exatamente as quatro tabelas de negócio abaixo. Tabelas auxiliares, views persistidas e duplicação de dados de negócio estão fora do escopo desta versão.

#### 1. `Clientes`

Representa a empresa compradora e a origem do limite de crédito.

| Campo | Tipo lógico | Regras |
|---|---|---|
| `id_cliente` | inteiro | Chave primária, obrigatória, única e imutável. |
| `razao_social` | texto | Obrigatória, não vazia. |
| `nome_fantasia` | texto | Opcional; quando informado, não pode ser vazio. |
| `cnpj` | texto | Obrigatório, único e armazenado em formato normalizado; deve conter documento empresarial válido. |
| `limite_credito` | decimal monetário | Obrigatório, maior ou igual a zero. |
| `status` | domínio enumerado | Obrigatório: `ativo`, `inativo` ou `bloqueado`. |
| `created_at` | data/hora | Obrigatória; preenchida na criação. |
| `updated_at` | data/hora | Obrigatória; atualizada a cada alteração autorizada. |

#### 2. `Pedidos`

Representa uma solicitação comercial feita por um cliente.

| Campo | Tipo lógico | Regras |
|---|---|---|
| `id_pedido` | inteiro | Chave primária, obrigatória, única e imutável. |
| `id_cliente` | inteiro | Chave estrangeira obrigatória para `Clientes.id_cliente`. |
| `data_pedido` | data/hora | Obrigatória. |
| `status` | domínio enumerado | Obrigatório: `pendente`, `confirmado`, `em_separacao`, `enviado`, `entregue` ou `cancelado`. |
| `valor_total` | decimal monetário | Obrigatório, maior ou igual a zero e igual à soma dos subtotais de seus itens. |
| `prazo_entrega_previsto` | data | Opcional até o pedido ser confirmado; não pode ser anterior a `data_pedido`. |
| `data_entrega_real` | data | Obrigatória quando `status` for `entregue`; nula nos demais estados não entregues. |
| `created_at` | data/hora | Obrigatória; preenchida na criação. |
| `updated_at` | data/hora | Obrigatória; atualizada a cada alteração autorizada. |

Relação: um registro de `Clientes` pode possuir zero ou muitos `Pedidos`; cada `Pedido` pertence a exatamente um `Cliente`.

#### 3. `Itens_Pedido`

Representa os produtos ou serviços registrados em um pedido. O cadastro de produtos não faz parte desta versão; a descrição é uma fotografia do item no momento do pedido.

| Campo | Tipo lógico | Regras |
|---|---|---|
| `id_item` | inteiro | Chave primária, obrigatória, única e imutável. |
| `id_pedido` | inteiro | Chave estrangeira obrigatória para `Pedidos.id_pedido`. |
| `codigo_produto` | texto | Obrigatório; identificador do produto no sistema de origem. |
| `descricao_produto` | texto | Obrigatória e não vazia. |
| `quantidade` | decimal | Obrigatória e maior que zero. |
| `preco_unitario` | decimal monetário | Obrigatório e maior ou igual a zero. |
| `desconto` | decimal monetário | Obrigatório, padrão zero, maior ou igual a zero e não superior ao valor bruto do item. |
| `subtotal` | decimal monetário | Obrigatório, não negativo, calculado como `quantidade * preco_unitario - desconto`. |

Relação: um `Pedido` deve possuir um ou mais `Itens_Pedido`; cada item pertence a exatamente um pedido. A exclusão de um pedido não pode deixar itens órfãos; a política de exclusão deve preservar histórico ou rejeitar a exclusão.

#### 4. `Faturas`

Representa uma cobrança emitida para um cliente, opcionalmente vinculada a um pedido.

| Campo | Tipo lógico | Regras |
|---|---|---|
| `id_fatura` | inteiro | Chave primária, obrigatória, única e imutável. |
| `numero_fatura` | texto | Obrigatório, único e normalizado. |
| `id_cliente` | inteiro | Chave estrangeira obrigatória para `Clientes.id_cliente`. |
| `id_pedido` | inteiro | Chave estrangeira opcional para `Pedidos.id_pedido`; quando informado, o pedido deve pertencer ao mesmo cliente. |
| `data_emissao` | data | Obrigatória. |
| `data_vencimento` | data | Obrigatória e igual ou posterior à emissão. |
| `valor_total` | decimal monetário | Obrigatório e maior ou igual a zero. |
| `valor_pago` | decimal monetário | Obrigatório, padrão zero, maior ou igual a zero e não superior ao valor total. |
| `status` | domínio enumerado | Obrigatório: `aberta`, `paga`, `vencida` ou `cancelada`. |
| `data_pagamento` | data | Obrigatória quando `status` for `paga`; nula nos demais estados. |
| `created_at` | data/hora | Obrigatória; preenchida na criação. |
| `updated_at` | data/hora | Obrigatória; atualizada a cada alteração autorizada. |

Relações: um `Cliente` pode possuir zero ou muitas `Faturas`; cada fatura pertence a exatamente um cliente. Um `Pedido` pode estar associado a zero ou muitas faturas, conforme parcelamento ou reemissão. Faturas canceladas permanecem disponíveis para auditoria, mas não entram em exposição ou inadimplência.

### Integridade e regras de negócio

- **FR-001**: O sistema DEVE manter somente as quatro entidades de negócio descritas: `Clientes`, `Pedidos`, `Itens_Pedido` e `Faturas`.
- **FR-002**: O sistema DEVE garantir chaves primárias, chaves estrangeiras, unicidade de `Clientes.cnpj` e `Faturas.numero_fatura` e rejeitar referências inexistentes.
- **FR-003**: O sistema DEVE impedir registros inválidos conforme os domínios, obrigatoriedade, limites numéricos e relações descritos para cada campo.
- **FR-004**: O sistema DEVE manter `Pedidos.valor_total` consistente com a soma de `Itens_Pedido.subtotal` e impedir pedido confirmado sem item válido.
- **FR-005**: O sistema DEVE manter a consistência entre `Faturas.id_cliente` e o cliente do pedido associado, quando `id_pedido` existir.
- **FR-006**: O sistema DEVE preservar pedidos e faturas para consulta histórica; nenhuma exclusão destrutiva pode ser feita pelo agente.
- **FR-007**: O acesso à persistência DEVE ocorrer exclusivamente por modelos tipados e repositórios dedicados; rotas e ferramentas do agente não podem instanciar modelos de persistência diretamente.
- **FR-008**: Consultas e alterações autorizadas DEVEM usar o ORM configurado pelo projeto e não podem conter strings de SQL puro.

### Regras de consulta do agente

- **FR-009**: O agente DEVE operar em modo de leitura para consultas de crédito, pedidos, itens e faturas. Simulações de status podem alterar apenas a resposta em memória e nunca persistir a simulação.
- **FR-010**: Toda ferramenta exposta ao modelo DEVE possuir docstring detalhada com finalidade, parâmetros, filtros permitidos, formato de resposta e limitações.
- **FR-011**: Antes de consultar, o agente DEVE resolver o cliente por `id_cliente` ou `cnpj`; nome parcial só pode ser usado para localizar candidatos e exige desambiguação quando houver mais de um resultado.
- **FR-012**: Toda consulta DEVE aplicar filtros por identificador de cliente, pedido ou fatura quando o contexto os fornecer; resultados de clientes diferentes não podem ser agregados sem solicitação explícita de relatório.
- **FR-013**: Consulta de crédito DEVE retornar: limite de crédito, exposição em aberto, saldo disponível, status do cliente e data de referência. A exposição em aberto é a soma de faturas não canceladas com `valor_total - valor_pago`; o saldo disponível é `max(0, limite_credito - exposição_em_aberto)`.
- **FR-014**: Consulta de pedidos DEVE permitir filtro por cliente, `id_pedido`, status e intervalo de datas, retornando status, total, itens resumidos, previsão de entrega e data real quando existente.
- **FR-015**: Consulta de entrega DEVE classificar como atrasado somente pedido não cancelado e não entregue cuja `prazo_entrega_previsto` seja anterior à data de referência; pedido entregue deve usar `data_entrega_real`.
- **FR-016**: Consulta de faturas vencidas DEVE considerar somente faturas não canceladas, não pagas integralmente e com `data_vencimento` anterior à data de referência. Deve retornar número, pedido relacionado, vencimento, dias de atraso, valor total e saldo em aberto.
- **FR-017**: Relatório de risco DEVE apresentar, por cliente solicitado, limite, exposição, faturas vencidas, maior atraso e pedidos em aberto, identificando dados ausentes ou inconsistentes em vez de inventar valores.
- **FR-018**: Consultas sem resultado DEVEM retornar resposta explícita de não encontrado; erros de negócio devem ser diferenciados de falhas técnicas e tratados conforme os códigos HTTP definidos pelo serviço.
- **FR-019**: Listagens DEVEM aceitar paginação e limite máximo definido pelo serviço; consultas por período DEVEM exigir ou aplicar uma janela padrão e informar o intervalo utilizado.
- **FR-020**: O agente DEVE informar a data de referência e a origem dos totais apresentados, sem expor campos sensíveis que não sejam necessários para responder à intenção.
- **FR-021**: O agente NÃO PODE criar, atualizar, excluir, liquidar ou cancelar registros durante uma consulta. Qualquer operação futura de escrita exige validação explícita no backend e não faz parte desta especificação.

### Key Entities

- **Cliente**: Empresa compradora, identificada por CNPJ, com limite e situação comercial.
- **Pedido**: Solicitação comercial de um cliente, com ciclo de atendimento e entrega.
- **Item de pedido**: Linha histórica de produto ou serviço dentro de um pedido, incluindo quantidade e valores.
- **Fatura**: Cobrança de um cliente, opcionalmente relacionada a um pedido e usada para apurar exposição e atraso.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Em pelo menos 95% das consultas de crédito com cliente identificado, o usuário recebe limite, exposição e saldo em até 2 segundos.
- **SC-002**: 100% dos pedidos e faturas retornados pelo agente respeitam as relações de cliente e não exibem registros de outro cliente no contexto solicitado.
- **SC-003**: 100% dos cenários de fatura vencida classificam corretamente faturas pagas, canceladas, vencendo hoje e vencidas.
- **SC-004**: Pelo menos 95% das consultas de pedido identificadas retornam status e informação de entrega sem exigir nova consulta manual.
- **SC-005**: 100% das tentativas de escrita iniciadas pelo agente durante consultas são bloqueadas e não modificam o banco.
- **SC-006**: Todos os registros aceitos respeitam as quatro relações e restrições de integridade definidas, conforme verificação automatizada de testes de integração.

## Assumptions

- O banco local do sistema é o repositório oficial para esta versão e os dados já chegam de uma fonte autorizada ou por carga controlada.
- Valores monetários são armazenados e exibidos com duas casas decimais; a moeda padrão é BRL.
- Datas e horários seguem uma referência única do serviço; a data de referência de uma consulta é a data corrente do serviço, salvo quando uma simulação informar outra data explicitamente.
- A autorização do usuário que chama o agente é validada fora desta especificação, mas os repositórios devem receber o contexto necessário para impedir acesso indevido.
- O ciclo de vida e a auditoria detalhada de alterações serão definidos em uma especificação posterior; esta versão exige apenas preservação do histórico e leitura segura.
- A entrega desta feature é o contrato de dados e de consulta; endpoints, modelos e migrações serão detalhados na fase de planejamento.
