from decimal import Decimal

from tests.integration.conftest import StubScorer, healthy_payload


def test_low_risk_application_is_approved(api_client):
    response = api_client.post("/applications", json=healthy_payload())
    assert response.status_code == 201
    decision = response.json()
    assert decision["outcome"] == "approved"
    assert decision["reasons"] == []
    assert Decimal(str(decision["monthly_payment"])) == Decimal("318.86")


def test_borderline_risk_needs_review(api_client, scorer: StubScorer):
    scorer.risk_score = 0.40
    response = api_client.post("/applications", json=healthy_payload())
    assert response.status_code == 201
    decision = response.json()
    assert decision["outcome"] == "needs_review"
    assert [reason["code"] for reason in decision["reasons"]] == ["borderline_risk"]


def test_hard_rule_failure_declines(api_client):
    payload = healthy_payload()
    payload["cafe"]["months_in_business"] = 2
    decision = api_client.post("/applications", json=payload).json()
    assert decision["outcome"] == "declined"
    assert [reason["code"] for reason in decision["reasons"]] == ["too_new"]


def test_invalid_payload_is_rejected_at_the_boundary(api_client):
    payload = healthy_payload()
    payload["equipment"]["price"] = "-5"
    assert api_client.post("/applications", json=payload).status_code == 422


def test_submitted_application_is_retrievable(api_client):
    application_id = api_client.post("/applications", json=healthy_payload()).json()[
        "application_id"
    ]
    detail = api_client.get(f"/applications/{application_id}").json()
    assert detail["cafe_name"] == "Sightglass Annex"
    assert detail["decision"]["application_id"] == application_id

    listing = api_client.get("/applications").json()
    assert len(listing) == 1


def test_unknown_application_returns_404(api_client):
    assert api_client.get("/applications/app_missing").status_code == 404
