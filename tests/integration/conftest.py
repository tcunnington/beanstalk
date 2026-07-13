"""Shared fixtures: a real service over tmp sqlite, with a deterministic scorer."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from beanstalk.domain.application import FinancingApplication
from beanstalk.interfaces.api.app import create_app as create_api_app
from beanstalk.interfaces.ui.app import create_app as create_ui_app
from beanstalk.services.applications import ApplicationService
from beanstalk.services.repository import DecisionRepository
from beanstalk.services.settings import Settings


class StubScorer:
    """Deterministic RiskScorer so tests control the decision outcome."""

    def __init__(self, risk_score: float = 0.10) -> None:
        self.risk_score = risk_score

    def score(self, application: FinancingApplication) -> float:
        return self.risk_score


@pytest.fixture
def scorer() -> StubScorer:
    return StubScorer()


@pytest.fixture
def service(tmp_path: Path, scorer: StubScorer):
    repository = DecisionRepository(tmp_path / "test.db")
    yield ApplicationService(repository, scorer, Settings())
    repository.close()


@pytest.fixture
def api_client(service: ApplicationService) -> TestClient:
    return TestClient(create_api_app(service))


@pytest.fixture
def ui_client(service: ApplicationService) -> TestClient:
    return TestClient(create_ui_app(service))


def healthy_payload() -> dict:
    return {
        "cafe": {
            "name": "Sightglass Annex",
            "months_in_business": 36,
            "monthly_revenue": "42000",
            "seats": 28,
            "has_existing_financing": False,
        },
        "equipment": {
            "category": "espresso_machine",
            "description": "La Marzocco Linea PB, 3 group",
            "price": "12000",
        },
        "term_months": 36,
        "down_payment": "2400",
    }
