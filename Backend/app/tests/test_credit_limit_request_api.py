from app.models.client import Client


def test_create_and_patch_credit_request_does_not_change_approved_limit(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    created = client.post(
        "/api/v1/clients/1/credit/requests",
        json={"requested_limit": 12000, "justification": "Expansão da operação"},
    )
    assert created.status_code == 201
    request_id = created.json()["id"]
    assert created.json()["current_limit"] == 5000
    assert created.json()["status"] == "PENDING"

    updated = client.patch(
        f"/api/v1/clients/1/credit/requests/{request_id}",
        json={"requested_limit": 15000},
    )
    assert updated.status_code == 200
    assert updated.json()["requested_limit"] == 15000

    deleted = client.delete(
        f"/api/v1/clients/1/credit/requests/{request_id}"
    )
    assert deleted.status_code == 204

    db.refresh(db.query(Client).filter_by(id=1).one())
    assert db.query(Client).filter_by(id=1).one().credit_limit == 5000

    openapi = client.get("/openapi.json").json()
    assert "post" in openapi["paths"]["/api/v1/clients/{id_cliente}/credit/requests"]
    assert "patch" in openapi["paths"]["/api/v1/clients/{id_cliente}/credit/requests/{request_id}"]
    assert "delete" in openapi["paths"]["/api/v1/clients/{id_cliente}/credit/requests/{request_id}"]


def test_patch_approves_request_and_updates_client_limit(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    created = client.post(
        "/api/v1/clients/1/credit/requests",
        json={"requested_limit": 12000, "justification": "Expansão da operação"},
    )
    request_id = created.json()["id"]

    approved = client.patch(
        f"/api/v1/clients/1/credit/requests/{request_id}",
        json={"status": "APPROVED"},
    )

    assert approved.status_code == 200
    assert approved.json()["status"] == "APPROVED"
    assert db.query(Client).filter_by(id=1).one().credit_limit == 12000


def test_patch_rejects_request_without_changing_client_limit(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    created = client.post(
        "/api/v1/clients/1/credit/requests",
        json={"requested_limit": 12000, "justification": "Expansão da operação"},
    )
    request_id = created.json()["id"]

    rejected = client.patch(
        f"/api/v1/clients/1/credit/requests/{request_id}",
        json={"status": "REJECTED"},
    )

    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    assert db.query(Client).filter_by(id=1).one().credit_limit == 5000


def test_patch_rejects_unknown_request_status(client, db):
    db.add(Client(
        id=1,
        cnpj="12345678000195",
        company_name="Cliente de Teste LTDA",
        status="ACTIVE",
        credit_limit=5000,
    ))
    db.commit()

    created = client.post(
        "/api/v1/clients/1/credit/requests",
        json={"requested_limit": 12000, "justification": "Expansão da operação"},
    )
    request_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/clients/1/credit/requests/{request_id}",
        json={"status": "INVALID"},
    )

    assert response.status_code == 422