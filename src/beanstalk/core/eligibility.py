"""Hard eligibility rules for financing applications.

Each rule is a pure function returning a Reason on failure or None on pass.
Any single failure is grounds for decline.
"""

from decimal import Decimal

from beanstalk.core.application import FinancingApplication
from beanstalk.core.decision import Reason
from beanstalk.utils.money import format_usd

MIN_MONTHS_IN_BUSINESS = 6
MIN_DOWN_PAYMENT_RATIO = Decimal("0.10")


def eligibility_failures(application: FinancingApplication) -> tuple[Reason, ...]:
    """Run every hard rule; return the reasons for all that failed."""
    rules = (_too_new_in_business, _term_outlives_equipment, _down_payment_too_small)
    return tuple(reason for rule in rules if (reason := rule(application)) is not None)


def _too_new_in_business(application: FinancingApplication) -> Reason | None:
    months = application.cafe.months_in_business
    if months >= MIN_MONTHS_IN_BUSINESS:
        return None
    return Reason(
        code="too_new",
        message=f"Cafe has operated {months} months; minimum is {MIN_MONTHS_IN_BUSINESS}.",
    )


def _term_outlives_equipment(application: FinancingApplication) -> Reason | None:
    lifetime = application.equipment.expected_lifetime_months
    if application.term_months <= lifetime:
        return None
    return Reason(
        code="term_outlives_equipment",
        message=(
            f"Term of {application.term_months} months exceeds the equipment's "
            f"expected {lifetime}-month life."
        ),
    )


def _down_payment_too_small(application: FinancingApplication) -> Reason | None:
    minimum = application.equipment.price * MIN_DOWN_PAYMENT_RATIO
    if application.down_payment >= minimum:
        return None
    return Reason(
        code="down_payment_too_small",
        message=(
            f"Down payment {format_usd(application.down_payment)} is below the "
            f"{MIN_DOWN_PAYMENT_RATIO:.0%} minimum of {format_usd(minimum)}."
        ),
    )
