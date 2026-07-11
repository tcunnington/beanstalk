from decimal import Decimal

import pytest

from beanstalk.utils.finmath import monthly_payment


def test_zero_rate_splits_principal_evenly():
    payment = monthly_payment(Decimal("1200"), annual_rate=Decimal("0"), term_months=12)
    assert payment == Decimal("100.00")


def test_standard_amortized_payment():
    payment = monthly_payment(Decimal("10000"), annual_rate=Decimal("0.12"), term_months=12)
    assert payment == Decimal("888.49")


def test_rejects_negative_principal():
    with pytest.raises(ValueError, match="principal"):
        monthly_payment(Decimal("-1"), annual_rate=Decimal("0.1"), term_months=12)


def test_rejects_non_positive_term():
    with pytest.raises(ValueError, match="term_months"):
        monthly_payment(Decimal("1000"), annual_rate=Decimal("0.1"), term_months=0)
