import pytest
from app.models.client import Client

@pytest.fixture(autouse=True)
def setup_client_data(db_session):
    """Cria o cliente base no banco em memória vazio antes dos testes."""
    cliente_teste = Client(
        id=1,  
        company_name="Empresa Teste LTDA",
        cnpj="12345678901234",
        credit_limit=5000.0,
        status="ACTIVE"
    )
    db_session.add(cliente_teste)
    db_session.commit()

def test_obter_credito_sucesso_200(client):
    """Testa o caminho feliz: cliente existe e a análise é retornada."""
    response = client.get("/api/v1/clients/1/credit")
    
    assert response.status_code == 200
    dados = response.json()
    assert dados["client_id"] == 1
    assert dados["available_credit"] == 5000.0 # Sem faturas, crédito total

def test_obter_credito_cliente_nao_encontrado_404(client):
    """Valida se o tratador de erros traduz NotFoundException para 404."""
    response = client.get("/api/v1/clients/999/credit")    
    assert response.status_code == 404
    assert "não encontrado" in response.json()["detail"]

def test_obter_credito_erro_de_validacao_422(client):
    """Valida se o Pydantic bloqueia dados do tipo errado na própria URL."""
    response = client.get("/api/v1/clients/abc/credit")
    
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Input should be a valid integer, unable to parse string as an integer"

def test_nao_mutacao_rota_get(client, db_session):
    """
    Garante o princípio de 'Safe Method' do HTTP GET.
    Usa o 'client' injetado para a requisição e o 'db_session' injetado para checar o banco.
    """
    response = client.get("/api/v1/clients/1/credit")
    assert response.status_code == 200
    
    # Verifica diretamente no banco utilizando a fixture db_session fornecida pelo conftest
    cliente = db_session.query(Client).filter(Client.id == 1).first()
    
    assert cliente.credit_limit == 5000.0
    assert cliente.status == "ACTIVE"
