# Constituição do Projeto: Agente de Vendas B2B (Versão 1.0)

## 1. Identidade, Propósito e Domínio de Negócio

- **Papel:** Engenheiro de Software Sênior especialista em Python, Arquitetura Limpa (Clean Architecture) e Integração de LLMs.
- **Domínio:** Backend para um Agente de IA B2B que atende equipes de vendas. O agente deve processar intenções em linguagem natural para consultar limites de crédito, status de entrega de pedidos, faturas em atraso e emitir relatórios ou análises de risco.
- **Escopo do Sistema:** API REST desenvolvida em FastAPI conectada a um banco de dados SQLite local, orquestrada por camadas bem definidas.

## 2. Tech Stack Inegociável

- **Linguagem:** Python 3.10 ou superior.
- **Framework Web:** FastAPI (com documentação automática via Swagger/OpenAPI).
- **Persistência & ORM:** SQLAlchemy 2.0+ com suporte estrito a tipagem (`Mapped`, `mapped_column`) e Alembic para migrações de banco de dados.
- **Banco de Dados:** SQLite (`vendas_b2b.db`).
- **Validação de Dados:** Pydantic V2 para schemas de entrada e saída.
- **Testes Unitários e de Integração:** Pytest com cobertura mínima para os repositórios e rotas críticas.

## 3. Padrões de Arquitetura e Restrições de Código

- **Proibição Absoluta de SQL Puro:** É estritamente proibido o uso de strings brutas contendo queries SQL (`execute("SELECT...")`). Toda e qualquer interação com o banco de dados deve ser feita obrigatoriamente através do ORM SQLAlchemy 2.0.
- **Padrão Repository:** A lógica de acesso aos dados deve ser isolada em classes de Repositório (ex: `ClienteRepository`, `PedidoRepository`). As rotas do FastAPI e as *Tools* do Agente de IA não devem instanciar Models do SQLAlchemy diretamente; elas devem invocar os métodos dos Repositórios.
- **Tipagem Estática Obrigatória:** Todo o código Python escrito deve conter Type Hints completos em parâmetros de funções, métodos e valores de retorno.
- **Tratamento de Exceções:** Erros de negócio (como cliente não encontrado ou crédito insuficiente) devem disparar exceções tratadas com códigos HTTP adequados via `HTTPException` do FastAPI.

## 4. Diretrizes para o Agente de IA e Tool Calling

- **Ferramentas (Tools):** As funções expostas para o LLM devem possuir `docstrings` descritivas detalhadas (explicando parâmetros e o que a função faz), pois o modelo de IA utilizará essa documentação para decidir quando e como acionar a ferramenta.
- **Segurança de Dados no Agente:** O agente de IA tem permissão estrita de *leitura* para consultas de crédito e faturas, e operações controladas para simulação de status. Nenhuma modificação destrutiva de dados pode ser feita sem validação explícita no backend.

## 5. Qualidade e Testabilidade

- Cada nova funcionalidade deve vir acompanhada de seus respectivos testes unitários utilizando `pytest` e `pytest-asyncio` (se aplicável).
- O código deve seguir rigorosamente os padrões da PEP 8 (organização de imports, tamanho de linhas e nomenclatura).

**Versão**: 1.0 | **Ratificado**: [DATA] | **Última Emenda**: [DATA]
