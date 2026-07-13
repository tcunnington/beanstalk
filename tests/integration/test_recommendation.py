"""The coordination tier delegating to a second feature (machine_recommender)."""

from decimal import Decimal

from beanstalk.core.application import EquipmentItem
from beanstalk.services.applications import ApplicationService
from tests.unit.builders import espresso_machine, healthy_cafe


def test_service_recommends_for_a_stored_applicant(service: ApplicationService):
    decision = service.submit(
        healthy_cafe(seats=30),
        espresso_machine(),
        term_months=36,
        down_payment=Decimal("2400"),
    )
    suggestion = service.recommend_machine(decision.application_id)
    assert isinstance(suggestion, EquipmentItem)
    assert suggestion.price > 0
