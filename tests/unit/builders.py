"""Builders for healthy domain test data; override fields per test."""

from decimal import Decimal
from typing import Any

from beanstalk.core.application import (
    CafeProfile,
    EquipmentCategory,
    EquipmentItem,
    FinancingApplication,
)


def healthy_cafe(**overrides: Any) -> CafeProfile:
    fields: dict[str, Any] = {
        "name": "Sightglass Annex",
        "months_in_business": 36,
        "monthly_revenue": Decimal("42000"),
        "seats": 28,
        "has_existing_financing": False,
    }
    return CafeProfile(**{**fields, **overrides})


def espresso_machine(**overrides: Any) -> EquipmentItem:
    fields: dict[str, Any] = {
        "category": EquipmentCategory.ESPRESSO_MACHINE,
        "description": "La Marzocco Linea PB, 3 group",
        "price": Decimal("12000"),
    }
    return EquipmentItem(**{**fields, **overrides})


def healthy_application(**overrides: Any) -> FinancingApplication:
    fields: dict[str, Any] = {
        "application_id": "app_test",
        "cafe": healthy_cafe(),
        "equipment": espresso_machine(),
        "term_months": 36,
        "down_payment": Decimal("2400"),
        "annual_rate": Decimal("0.12"),
    }
    return FinancingApplication(**{**fields, **overrides})
