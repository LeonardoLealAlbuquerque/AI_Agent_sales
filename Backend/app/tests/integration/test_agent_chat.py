from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.agent import get_llm_client
from app.agent.llm_client import MockLLMClient
from app.db.base import Base  # Importe o Base contendo os metadados das tabelas
from app.models.client import Client
from app.models.order import Order, OrderStatus
from app.models.invoice import Invoice


client = TestClient(app)


@pytest.fixture(autouse=True)
def seed_agent_data(db, monkeypatch):
    """Cria as tabelas no SQLite em memória e popula os dados iniciais do agente."""
    # Garante a criação de todas as tabelas (clients, orders, invoices, etc.)
    Base.metadata.create_all(bind=db.get_bind())

    hoje = date.today()
    db.add(Client(
        id=1,
        company_name="Empresa Teste LTDA",
        cnpj="12345678901234",
        credit_limit=5000.0,
        status="ACTIVE",
    ))
    db.add(Order(
        id=1,
        client_id=1,
        status=OrderStatus.PENDING,
        total_amount=100.0,
        created_at=hoje,
        estimated_delivery_date=hoje + timedelta(days=7),
    ))
    db.commit()

    def override_get_db():
        # As ferramentas são chamadas diretamente pelo orquestrador, fora do
        # ciclo de dependências do FastAPI. Elas precisam usar a mesma sessão
        # que foi criada e populada por esta fixture.
        yield db

    monkeypatch.setattr("app.api.tools.get_db", override_get_db)


# --- Helper Classes para Simulação de Respostas do Mock ---
class MockToolCallFunction:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments

class MockToolCall:
    def __init__(self, call_id: str, name: str, arguments: str):
        self.id = call_id
        self.function = MockToolCallFunction(name, arguments)

class MockMessage:
    def __init__(self, content: str = None, tool_calls: list = None):
        self.content = content
        self.tool_calls = tool_calls or []

class MockChoice:
    def __init__(self, message: MockMessage):
        self.message = message

class MockResponse:
    def __init__(self, message: MockMessage):
        self.choices = [MockChoice(message)]


# --- Testes de Integração do Agente ---

def test_chat_direct_response():
    """Testa resposta textual direta do LLM sem acionamento de ferramentas."""
    mock_llm = MockLLMClient(
        canned_response=MockResponse(MockMessage(content="Olá! Como posso ajudar na análise de crédito hoje?"))
    )
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    payload = {"message": "Olá, bom dia!"}
    response = client.post("/api/v1/agent/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Olá! Como posso ajudar na análise de crédito hoje?"
    assert len(data["tools_used"]) == 0
    app.dependency_overrides.clear()

@pytest.mark.parametrize("tool_name,args_json", [
    ("get_client_risk_analysis", '{"client_id": 1}'),
    ("get_client_credit_limit", '{"client_id": 1}'),
    ("get_overdue_invoices", '{"client_id": 1}'),
    ("get_client_orders", '{"client_id": 1}'),
    ("get_order_details", '{"order_id": 1}')
])
def test_chat_tool_execution(tool_name, args_json):
    """Testa a chamada e o retorno individual de cada uma das 5 ferramentas mapeadas."""
    tool_call = MockToolCall("call_1", tool_name, args_json)
    
    class MultiTurnMockClient(MockLLMClient):
        def __init__(self):
            super().__init__()
            self.turn = 0

        def chat_completion(self, messages, tools=None):
            self.turn += 1
            if self.turn == 1:
                return MockResponse(MockMessage(content=None, tool_calls=[tool_call]))
                
            return MockResponse(MockMessage(content=f"Análise concluída via {tool_name}."))

    app.dependency_overrides[get_llm_client] = lambda: MultiTurnMockClient()

    payload = {"message": f"Executar consulta para {tool_name}"}

    # Executa a requisição diretamente sem tentar mockar a constante TOOLS_MAP
    response = client.post("/api/v1/agent/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data["tools_used"]) == 1
    assert data["tools_used"][0]["tool_name"] == tool_name
    assert data["tools_used"][0]["success"] is True
    app.dependency_overrides.clear()

def test_chat_unknown_tool_and_invalid_arguments():
    """Testa a resiliência a ferramentas desconhecidas ou argumentos malformados."""
    tool_call = MockToolCall("call_bad", "ferramenta_inexistente", "invalid json")

    class BadToolMockClient(MockLLMClient):
        def __init__(self):
            super().__init__()
            self.turn = 0

        def chat_completion(self, messages, tools=None):
            self.turn += 1
            if self.turn == 1:
                return MockResponse(MockMessage(content=None, tool_calls=[tool_call]))
            return MockResponse(MockMessage(content="Não consegui executar essa ação."))

    app.dependency_overrides[get_llm_client] = lambda: BadToolMockClient()

    payload = {"message": "Tente rodar uma ferramenta inválida"}
    response = client.post("/api/v1/agent/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["tools_used"][0]["success"] is False
    app.dependency_overrides.clear()


def test_chat_llm_timeout_handling():
    """Testa o mapeamento correto de timeout do provedor LLM para HTTP 504."""
    mock_llm = MockLLMClient(should_timeout=True)
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    payload = {"message": "Qual o limite de crédito do cliente 1?"}
    response = client.post("/api/v1/agent/chat", json=payload)

    assert response.status_code == 504
    assert "excedeu o tempo limite" in response.json()["detail"]
    app.dependency_overrides.clear()


def test_chat_llm_unavailable_handling():
    """Testa o mapeamento correto de indisponibilidade do provedor para HTTP 503."""
    mock_llm = MockLLMClient(should_fail=True)
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    payload = {"message": "Qual o limite de crédito do cliente 1?"}
    response = client.post("/api/v1/agent/chat", json=payload)

    assert response.status_code == 503
    assert "indisponível" in response.json()["detail"]
    app.dependency_overrides.clear()


def test_chat_write_attempt_refusal():
    """Valida se o LLM recusa tentativas de escrita/mutação via instruções de Prompt."""
    refusal_msg = "Minhas permissões são limitadas à consulta de dados (Read-Only). Não posso alterar cadastros."
    mock_llm = MockLLMClient(
        canned_response=MockResponse(MockMessage(content=refusal_msg))
    )
    app.dependency_overrides[get_llm_client] = lambda: mock_llm

    payload = {"message": "Aumente o limite de crédito do cliente 1 para R$ 500.000"}
    response = client.post("/api/v1/agent/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "Read-Only" in data["response"] or "não posso" in data["response"].lower()
    assert len(data["tools_used"]) == 0
    app.dependency_overrides.clear()
