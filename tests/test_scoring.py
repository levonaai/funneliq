from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_LEAD = {
    "ad_budget": 3000,
    "num_leads": 40,
    "leads_answered": 27,
    "leads_not_answered": 13,
    "followup_1": 21,
    "followup_2": 15,
    "followup_3": 13,
    "followup_4": 11,
    "followup_5": 8,
    "not_closed": 5,
    "closed": 3,
    "calls_to_closed": 3,
    "calls_to_not_closed": 4,
    "customer_acquisition_cost": 1000,
    "ltv_months": 21.0,
    "purchased": 1,
    "upsell": 0,
}


def test_score_lead_without_token_returns_401() -> None:
    response = client.post("/api/score-lead", json=VALID_LEAD)
    assert response.status_code == 401


def test_score_lead_with_valid_token_returns_score_in_range(make_token) -> None:
    token = make_token()
    response = client.post(
        "/api/score-lead", json=VALID_LEAD, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    score = response.json()["super_customer_score"]
    assert 0.0 <= score <= 100.0
