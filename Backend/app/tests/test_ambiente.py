def test_banco_em_memoria_inicia_corretamente(db_session):
    assert db_session is not None