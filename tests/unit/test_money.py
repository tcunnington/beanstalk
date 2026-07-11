from decimal import Decimal

from beanstalk.utils.money import format_usd, round_cents


def test_round_cents_uses_bankers_rounding():
    assert round_cents(Decimal("2.675")) == Decimal("2.68")
    assert round_cents(Decimal("2.665")) == Decimal("2.66")
    assert round_cents(Decimal("2.5")) == Decimal("2.50")


def test_format_usd_adds_symbol_and_thousands_separators():
    assert format_usd(Decimal("12345.678")) == "$12,345.68"
    assert format_usd(Decimal("0")) == "$0.00"
