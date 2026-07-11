"""Generic financial math. Pure functions with no business context."""

from decimal import Decimal

from beanstalk.utils.money import round_cents

MONTHS_PER_YEAR = 12


def monthly_payment(principal: Decimal, *, annual_rate: Decimal, term_months: int) -> Decimal:
    """Standard amortized (annuity) monthly payment for a loan.

    Returns the fixed monthly payment that repays ``principal`` plus interest
    at ``annual_rate`` (a fraction, e.g. ``Decimal("0.12")``) over
    ``term_months`` equal installments.
    """
    if principal < 0:
        raise ValueError(f"principal must be non-negative, got {principal}")
    if term_months <= 0:
        raise ValueError(f"term_months must be positive, got {term_months}")
    monthly_rate = annual_rate / MONTHS_PER_YEAR
    if monthly_rate == 0:
        return round_cents(principal / term_months)
    growth = (1 + monthly_rate) ** term_months
    return round_cents(principal * monthly_rate * growth / (growth - 1))
