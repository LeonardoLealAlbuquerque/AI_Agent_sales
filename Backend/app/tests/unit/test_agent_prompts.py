from app.agent.prompts import B2B_SALES_AGENT_SYSTEM_PROMPT


def test_system_prompt_explains_exposure_warning_without_claiming_account_block():
    assert "exposição das faturas pendentes supera o limite de crédito aprovado" in (
        B2B_SALES_AGENT_SYSTEM_PROMPT
    )
    assert "não como bloqueio automático" in B2B_SALES_AGENT_SYSTEM_PROMPT
    assert "tom profissional e proporcional" in B2B_SALES_AGENT_SYSTEM_PROMPT


def test_system_prompt_uses_risk_alerts_without_reclassifying_or_inventing_block():
    assert "Não recalcule nem reclassifique o nível por conta própria." in (
        B2B_SALES_AGENT_SYSTEM_PROMPT
    )
    assert "Para `EXPOSICAO_ELEVADA`" in B2B_SALES_AGENT_SYSTEM_PROMPT
    assert "Para `ATRASO_CRITICO`" in B2B_SALES_AGENT_SYSTEM_PROMPT
    assert "só afirme que o cliente está bloqueado" in (
        B2B_SALES_AGENT_SYSTEM_PROMPT
    )
    assert "não como garantia de ausência de risco" in B2B_SALES_AGENT_SYSTEM_PROMPT
