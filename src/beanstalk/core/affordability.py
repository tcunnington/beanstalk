"""Affordability policy: can the cafe's revenue support the monthly payment?

Business policy built on the generic annuity math in utils.finmath — a
Tier 1 -> Tier 2 build-up.
"""

from decimal import Decimal

from beanstalk.core.application import FinancingApplication
from beanstalk.core.decision import Reason
from beanstalk.utils.finmath import monthly_payment

MAX_PAYMENT_TO_REVENUE = Decimal("0.15")


def monthly_payment_for(application: FinancingApplication) -> Decimal:
    """The fixed monthly payment this application implies."""
    return monthly_payment(
        application.financed_amount,
        annual_rate=application.annual_rate,
        term_months=application.term_months,
    )


def affordability_failure(application: FinancingApplication) -> Reason | None:
    """Check the payment-to-revenue cap; return a Reason on failure."""
    revenue = application.cafe.monthly_revenue
    if revenue <= 0:
        return Reason(code="no_revenue", message="Cafe reports no monthly revenue.")
    payment_ratio = monthly_payment_for(application) / revenue
    if payment_ratio <= MAX_PAYMENT_TO_REVENUE:
        return None
    return Reason(
        code="unaffordable",
        message=(
            f"Payment is {payment_ratio:.0%} of monthly revenue; "
            f"cap is {MAX_PAYMENT_TO_REVENUE:.0%}."
        ),
    )
