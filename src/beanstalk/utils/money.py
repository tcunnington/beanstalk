"""Decimal amount helpers: rounding and display formatting."""

from decimal import ROUND_HALF_EVEN, Decimal

_CENTS = Decimal("0.01")


def round_cents(amount: Decimal) -> Decimal:
    """Quantize an amount to two decimal places using banker's rounding."""
    return amount.quantize(_CENTS, rounding=ROUND_HALF_EVEN)


def format_usd(amount: Decimal) -> str:
    """Format an amount as a US dollar string, e.g. ``$12,345.67``."""
    return f"${round_cents(amount):,}"
