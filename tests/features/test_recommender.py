"""The machine_recommender feature, tested in isolation through its entrypoint."""

from decimal import Decimal

from beanstalk.core.application import EquipmentCategory
from beanstalk.features.machine_recommender.entrypoint import load_recommender
from tests.unit.builders import healthy_cafe


def test_recommends_a_bigger_machine_for_more_seats():
    recommender = load_recommender()
    small = recommender.recommend(healthy_cafe(seats=8))
    large = recommender.recommend(healthy_cafe(seats=60))
    assert large.price > small.price
    assert large.category is EquipmentCategory.ESPRESSO_MACHINE


def test_recommendation_is_a_core_equipment_item():
    suggestion = load_recommender().recommend(healthy_cafe(seats=24))
    assert suggestion.price > Decimal("0")
    assert suggestion.description  # carries the model name + rationale
