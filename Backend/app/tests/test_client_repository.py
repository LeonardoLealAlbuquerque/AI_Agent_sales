import json
import pytest
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientFilterParams


@pytest.fixture(autouse=True)
def seed_client_repository_data(db_session):
    """Adiciona dados específicos usando a mesma sessão compartilhada da suíte."""
    db_session.add_all([
        Client(id=2, cnpj="11111111111111", company_name="Tech Solutions LTDA", status="ACTIVE", credit_limit=5000.0),
        Client(id=3, cnpj="22222222222222", company_name="Global tech Inovações", status="ACTIVE", credit_limit=10000.0),
        Client(id=4, cnpj="33333333333333", company_name="Construtora Alfa", status="INACTIVE", credit_limit=0.0),
    ])
    db_session.commit()


# Casos de teste


def test_get_by_cnpj_identificacao_exata(db_session):
    """Testa a identificação precisa de um cliente pelo CNPJ."""
    repo = ClientRepository(db_session)
    
    cliente = repo.get_by_cnpj("11111111111111")
    
    assert cliente is not None
    assert cliente.company_name == "Tech Solutions LTDA"

def test_get_by_nome_parcial_ambiguidade(db_session):
    """
    Testa a desambiguação: deve ignorar maiúsculas/minúsculas e 
    encontrar a palavra em qualquer lugar do nome da empresa.
    """
    repo = ClientRepository(db_session)
    
    # Buscando por "tECh" de forma totalmente despadronizada
    clientes = repo.get_by_partial_name("tECh")
    
    assert len(clientes) == 2
    nomes = [c.company_name for c in clientes]
    assert "Tech Solutions LTDA" in nomes
    assert "Global tech Inovações" in nomes

def test_get_by_id_identificacao_herdada(db_session):
    """Testa se o método genérico herdado de BaseRepository funciona."""
    repo = ClientRepository(db_session)
    
    cliente = repo.get_by_id(3)

    assert cliente is not None
    assert cliente.cnpj == "22222222222222"


def test_isolamento_nenhum_registro_encontrado(db_session):
    """Garante que buscas inválidas não quebram o código, apenas retornam vazio."""
    repo = ClientRepository(db_session)
    
    cliente_por_cnpj = repo.get_by_cnpj("99999999999999")
    clientes_por_nome = repo.get_by_partial_name("Empresa Inexistente")
    
    assert cliente_por_cnpj is None
    assert len(clientes_por_nome) == 0


def test_get_filtered_clients_combina_cnpj_limite_e_status(db_session):
    repo = ClientRepository(db_session)

    clientes = repo.get_filtered_clients(ClientFilterParams(
        cnpj="333.333.333-33",
        credit_limit=0,
        status="inactive",
    ))

    assert len(clientes) == 1
    assert clientes[0].id == 4


def test_get_filtered_clients_filtra_por_faixa_de_limite_e_pagina(db_session):
    repo = ClientRepository(db_session)

    clientes = repo.get_filtered_clients(ClientFilterParams(
        min_credit_limit=5000,
        max_credit_limit=10000,
        status="ACTIVE",
        limit=1,
        skip=1,
    ))

    assert len(clientes) == 1
    assert clientes[0].id == 3


def test_tool_list_clients_filtra_atributos_e_expoe_schema(db_session, monkeypatch):
    from app import api
    from app.agent.tools import GROQ_TOOL_SCHEMAS, execute_tool

    monkeypatch.setattr(api.tools, "get_db", lambda: iter([db_session]))
    client_tool = next(
        tool["function"] for tool in GROQ_TOOL_SCHEMAS
        if tool["function"]["name"] == "list_clients"
    )
    assert {"cnpj", "credit_limit", "status"}.issubset(
        client_tool["parameters"]["properties"]
    )

    result = json.loads(execute_tool("list_clients", {
        "cnpj": "333.333.333-33",
        "credit_limit": 0,
        "status": "inactive",
    }))

    assert result["total_clients"] == 1
    assert result["clients"][0]["id"] == 4


