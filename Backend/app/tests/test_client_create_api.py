def test_create_client_endpoint_and_openapi_schema(client):
    response = client.post(
        "/api/v1/clients",
        json={
            "company_name": "  Nova Empresa LTDA  ",
            "cnpj": "12.345.678/0001-95",
            "credit_limit": 2500,
        },
    )

    assert response.status_code == 201
    assert response.json()["company_name"] == "Nova Empresa LTDA"
    assert response.json()["cnpj"] == "12345678000195"
    assert response.json()["credit_limit"] == 2500
    assert response.json()["status"] == "ACTIVE"

    openapi = client.get("/openapi.json").json()
    operation = openapi["paths"]["/api/v1/clients"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"] == (
        "#/components/schemas/ClientCreate"
    )
    assert "201" in operation["responses"]


def test_create_client_rejects_duplicate_cnpj(client):
    payload = {
        "company_name": "Empresa Original",
        "cnpj": "12345678000195",
        "credit_limit": 1000,
    }
    first_response = client.post("/api/v1/clients", json=payload)
    duplicate_response = client.post(
        "/api/v1/clients",
        json={**payload, "company_name": "Empresa Duplicada"},
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 400
    assert "CNPJ" in duplicate_response.json()["detail"]


def test_create_client_rejects_invalid_cnpj(client):
    response = client.post(
        "/api/v1/clients",
        json={"company_name": "Empresa", "cnpj": "123", "credit_limit": 0},
    )

    assert response.status_code == 422