# Agente de Vendas B2B

Aplicação web para apoiar equipes comerciais B2B em consultas sobre clientes, crédito, faturas, pedidos e políticas de negociação. A interface permite conversar em linguagem natural com um agente de IA; a API também disponibiliza operações REST para consultar e manter dados comerciais.

## Funcionalidades

- **Chat com agente de vendas:** responde a perguntas sobre clientes, exposição e risco de crédito, faturas, pedidos e regras comerciais. As respostas são transmitidas progressivamente para a interface.
- **Histórico de conversas:** cria conversas, recupera mensagens, lista as conversas recentes e permite excluí-las.
- **Consultas comerciais:** pesquisa clientes e faturas com filtros; consulta pedidos e seus itens.
- **Crédito e risco:** calcula exposição financeira, crédito disponível e indicadores de atraso, bloqueio e risco.
- **Operações de cadastro:** permite cadastrar clientes, pedidos, itens de pedidos e faturas, além de manter solicitações pendentes de revisão de limite de crédito.
- **Base de conhecimento:** o agente pode buscar trechos do playbook B2B armazenado em uma coleção vetorial ChromaDB.
- **Interface responsiva:** inclui uma área de chat, histórico lateral e visualização de mensagens com suporte a Markdown.

O cálculo consolidado de risco inclui exposição, maior atraso e inconsistências. Os campos de pedidos em aberto dessa análise ainda não são integrados ao cálculo e são retornados como zero.

## Tecnologias e bibliotecas

### Backend

- **Python**, **FastAPI** e **Uvicorn** para a API HTTP e execução do servidor.
- **Pydantic** e **pydantic-settings** para validação de dados e configuração por variáveis de ambiente.
- **SQLAlchemy** e **SQLite** como camada ORM e banco padrão; **Alembic** para migrações.
- **Groq SDK** para chamadas ao modelo de linguagem (LLM).
- **LangChain Core** para definir ferramentas que o agente pode invocar.
- **ChromaDB** e **LangChain Text Splitters** para a base de conhecimento vetorial.
- **pytest** e **HTTPX** para testes.

### Frontend

- **React 19**, **TypeScript** e **React Router**.
- **Vite** para desenvolvimento e build, com os plugins React e Tailwind CSS.
- **Tailwind CSS 4** para estilos.
- **react-markdown**, **remark-gfm**, **rehype-raw** e **rehype-sanitize** para renderizar Markdown e conteúdo compatível com GitHub Flavored Markdown.
- **Vitest**, **jsdom** e **Testing Library** para testes; **ESLint** para lint.

## Rotas

A API usa o prefixo `/api/v1`. O FastAPI também publica a documentação interativa em `/docs`, a documentação alternativa em `/redoc` e o schema em `/openapi.json`.

### Saúde

| Método | Rota | Funcionalidade |
| --- | --- | --- |
| `GET` | `/health` | Informa se a API está operando. |

### Clientes

| Método | Rota | Funcionalidade |
| --- | --- | --- |
| `POST` | `/api/v1/clients` | Cadastra cliente; o CNPJ é normalizado e deve ser único. |

### Crédito e risco

| Método | Rota | Funcionalidade |
| --- | --- | --- |
| `GET` | `/api/v1/clients/{id_cliente}/credit` | Retorna limite, exposição, crédito disponível e motivos de bloqueio. |
| `POST` | `/api/v1/clients/{id_cliente}/credit/requests` | Registra uma solicitação de revisão de limite sem alterar o limite aprovado. |
| `PATCH` | `/api/v1/clients/{id_cliente}/credit/requests/{request_id}` | Atualiza uma solicitação ainda pendente. |
| `DELETE` | `/api/v1/clients/{id_cliente}/credit/requests/{request_id}` | Remove uma solicitação ainda pendente. |
| `GET` | `/api/v1/clients/{client_id}/risk` | Retorna risco consolidado, exposição, maior atraso e inconsistências. |

### Pedidos

| Método | Rota | Funcionalidade |
| --- | --- | --- |
| `POST` | `/api/v1/orders` | Cria um pedido para cliente existente, incluindo os itens. |
| `GET` | `/api/v1/clients/{client_id}/orders` | Lista pedidos de um cliente; aceita `skip` e `limit`. |
| `GET` | `/api/v1/orders/{pedido_id}` | Consulta o pedido com seus itens e informação de entrega. |
| `POST` | `/api/v1/orders/{order_id}/items` | Adiciona item a um pedido. |
| `PATCH` | `/api/v1/orders/{order_id}/items/{item_id}` | Atualiza item e recalcula o total. |
| `DELETE` | `/api/v1/orders/{order_id}/items/{item_id}` | Remove item e recalcula o total; o pedido precisa manter pelo menos um item. |

### Faturas

| Método | Rota | Funcionalidade |
| --- | --- | --- |
| `POST` | `/api/v1/invoices` | Cadastra uma fatura para cliente existente. |
| `GET` | `/api/v1/invoices/invoices` | Lista faturas agrupadas por cliente; permite filtrar por busca, cliente, status, vencimento, valores e datas de pagamento. |
| `GET` | `/api/v1/clients/{client_id}/invoices/summary?start=AAAA-MM-DD&end=AAAA-MM-DD` | Resume os valores pagos, pendentes e cancelados no período informado. |

### Agente e conversas

| Método | Rota | Funcionalidade |
| --- | --- | --- |
| `POST` | `/api/v1/agent/chat` | Envia mensagem ao agente; aceita `message`, `conversation_id` opcional e `history` opcional. A resposta é transmitida em streaming. |
| `GET` | `/api/v1/agent/conversations` | Lista conversas; aceita `limit` entre 1 e 100 (padrão 50). |
| `GET` | `/api/v1/agent/conversations/{conversation_id}` | Recupera o histórico de mensagens de uma conversa. |
| `DELETE` | `/api/v1/agent/conversations/{conversation_id}` | Exclui a conversa do histórico. |

O agente pode usar ferramentas para pesquisar clientes, analisar risco e crédito, consultar faturas e pedidos, obter detalhes de um pedido e buscar regras de negociação. Erros de validação e regras de negócio são reportados pela API com códigos HTTP apropriados.

> **Observação:** a rota de listagem de faturas está atualmente publicada como `/api/v1/invoices/invoices` pela composição dos roteadores. A documentação interativa em `/docs` mostra o contrato efetivamente carregado pela aplicação.

### Rotas da interface web

- `/` abre uma conversa nova.
- `/{conversationId}` abre uma conversa existente pelo identificador.

## Pré-requisitos

- Python 3.10 ou superior.
- Node.js e npm, em versões compatíveis com o Vite 8.
- Uma chave de API válida da Groq e um modelo disponível na conta.

## Como executar

Abra dois terminais na raiz do repositório.

### 1. Instalar e iniciar o backend

No primeiro terminal, no PowerShell:

```powershell
cd Backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Crie `Backend/.env` com as configurações necessárias:

```dotenv
LLM_API_KEY=sua_chave_groq
LLM_MODEL=seu_modelo_disponivel_na_groq
```

`LLM_API_KEY` é obrigatória. `LLM_MODEL` deve indicar um modelo aceito pela Groq; se omitida, a configuração do projeto usa `gpt-4o` como padrão, que pode não estar disponível nesse provedor. Não compartilhe nem versione sua chave.

Para criar as tabelas e inserir dados demonstrativos opcionais:

```powershell
python scripts/seed_demo.py
```

O script cria as tabelas no banco configurado em `DATABASE_URL` ou, por padrão, em `Backend/app.db`. Se o banco já contiver clientes, a carga demonstrativa é ignorada.

Inicie a API a partir do diretório `Backend`:

```powershell
python -m uvicorn app.main:app --reload
```

A API ficará disponível em `http://localhost:8000`. Consulte os endpoints em `http://localhost:8000/docs`.

### 2. Instalar e iniciar o frontend

No segundo terminal:

```powershell
cd Frontend
npm install
npm run dev
```

O Vite informa no terminal o endereço local da interface (normalmente `http://localhost:5173`). Por padrão, o frontend chama a API em `http://localhost:8000`. Para apontar para outra URL, defina `VITE_API_BASE_URL` no ambiente do Vite ou em um arquivo local `Frontend/.env.local`, por exemplo:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

## Banco de dados e configuração

- O backend usa SQLite por padrão, com caminho relativo ao diretório em que o servidor é iniciado: `sqlite:///./app.db`.
- `DATABASE_URL` permite configurar outra URL SQLAlchemy.
- A base vetorial do ChromaDB usa o armazenamento persistente em `Backend/data/chroma/`.
- As configurações do modelo incluem `LLM_API_KEY`, `LLM_MODEL`, `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_TIMEOUT` e `LLM_MAX_TOKENS`. A integração efetiva do cliente LLM no código usa o SDK da Groq.
- O CORS da API está configurado para origens locais comuns: portas 5173 e 3000.

## Testes, lint e build

Backend, a partir de `Backend` e com o ambiente virtual ativado:

```powershell
pytest
```

Frontend, a partir de `Frontend`:

```powershell
npm run lint
npm run build
```

## Estrutura do repositório

```text
Backend/
  app/
    agent/       Orquestração do agente, cliente LLM, prompts e ferramentas
    api/         Rotas, dependências e tratamento de erros HTTP
    core/        Configuração
    db/          Base ORM e sessão SQLAlchemy
    models/      Modelos de persistência
    repositories/ Acesso a dados
    schemas/     Contratos e validação de entrada/saída
    services/    Regras de negócio
    tests/       Testes unitários, de API e integração
  docs/          Playbook de negociação B2B
  scripts/       Utilitários, incluindo carga demonstrativa
  alembic/       Migrações do banco
Frontend/
  src/
    components/  Componentes de chat e navegação
    services/    Comunicação com a API
    types/       Tipos TypeScript
```
