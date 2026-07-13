from decimal import Decimal

from beanstalk.core.decision import DecisionOutcome
from beanstalk.services.applications import ApplicationService
from tests.integration.conftest import StubScorer
from tests.unit.builders import espresso_machine, healthy_cafe


def submit_borderline(service: ApplicationService, scorer: StubScorer) -> str:
    scorer.risk_score = 0.40
    decision = service.submit(
        healthy_cafe(),
        espresso_machine(),
        term_months=36,
        down_payment=Decimal("2400"),
    )
    return decision.application_id


def test_queue_lists_applications_needing_review(ui_client, service, scorer):
    submit_borderline(service, scorer)
    page = ui_client.get("/")
    assert page.status_code == 200
    assert "Sightglass Annex" in page.text
    assert "Needs review (1)" in page.text


def test_reviewer_approval_resolves_the_decision(ui_client, service, scorer):
    application_id = submit_borderline(service, scorer)
    response = ui_client.post(
        f"/applications/{application_id}/review",
        data={"verdict": "approve", "note": "Solid revenue, known roaster."},
        follow_redirects=False,
    )
    assert response.status_code == 303

    _, decision = service.get(application_id)
    assert decision.outcome is DecisionOutcome.APPROVED
    assert decision.reasons[-1].code == "manual_review"


def test_review_on_settled_application_conflicts(ui_client, service, scorer):
    application_id = submit_borderline(service, scorer)
    review_url = f"/applications/{application_id}/review"
    ui_client.post(review_url, data={"verdict": "decline"}, follow_redirects=False)
    second = ui_client.post(review_url, data={"verdict": "approve"}, follow_redirects=False)
    assert second.status_code == 409


def test_invalid_verdict_is_rejected_at_the_boundary(ui_client, service, scorer):
    application_id = submit_borderline(service, scorer)
    response = ui_client.post(
        f"/applications/{application_id}/review",
        data={"verdict": "maybe"},
        follow_redirects=False,
    )
    assert response.status_code == 422


def test_detail_page_shows_reasons_and_review_form(ui_client, service, scorer):
    application_id = submit_borderline(service, scorer)
    page = ui_client.get(f"/applications/{application_id}")
    assert "borderline_risk" in page.text
    assert "Approve" in page.text


def test_unknown_application_404s(ui_client):
    assert ui_client.get("/applications/app_missing").status_code == 404
