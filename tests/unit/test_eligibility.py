from decimal import Decimal

from beanstalk.core.eligibility import eligibility_failures
from tests.unit.builders import healthy_application, healthy_cafe


def failure_codes(application) -> set[str]:
    return {reason.code for reason in eligibility_failures(application)}


def test_healthy_application_passes_all_rules():
    assert eligibility_failures(healthy_application()) == ()


def test_cafe_too_new_in_business_fails():
    application = healthy_application(cafe=healthy_cafe(months_in_business=3))
    assert failure_codes(application) == {"too_new"}


def test_term_longer_than_equipment_life_fails():
    application = healthy_application(term_months=200)  # espresso machine lives 120 months
    assert failure_codes(application) == {"term_outlives_equipment"}


def test_down_payment_below_ten_percent_fails():
    application = healthy_application(down_payment=Decimal("1000"))  # price is 12000
    assert failure_codes(application) == {"down_payment_too_small"}


def test_multiple_failures_all_reported():
    application = healthy_application(
        cafe=healthy_cafe(months_in_business=1),
        down_payment=Decimal("0"),
    )
    assert failure_codes(application) == {"too_new", "down_payment_too_small"}
