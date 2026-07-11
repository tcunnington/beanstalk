from decimal import Decimal

from beanstalk.domain.affordability import affordability_failure, monthly_payment_for
from tests.unit.builders import healthy_application, healthy_cafe


def test_healthy_application_is_affordable():
    assert affordability_failure(healthy_application()) is None


def test_payment_over_revenue_cap_fails():
    # Payment on 9600 @ 12% over 36 months is ~318.86; 16% of 2000 revenue.
    application = healthy_application(cafe=healthy_cafe(monthly_revenue=Decimal("2000")))
    failure = affordability_failure(application)
    assert failure is not None
    assert failure.code == "unaffordable"


def test_no_revenue_fails_outright():
    application = healthy_application(cafe=healthy_cafe(monthly_revenue=Decimal("0")))
    failure = affordability_failure(application)
    assert failure is not None
    assert failure.code == "no_revenue"


def test_monthly_payment_matches_amortization_of_financed_amount():
    payment = monthly_payment_for(healthy_application())
    assert payment == Decimal("318.86")
