"""Core data shapes for a financing application.

These are anemic by design: methods are limited to derived properties.
Business rules live in eligibility.py / affordability.py / decisioning.py.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class EquipmentCategory(StrEnum):
    ESPRESSO_MACHINE = "espresso_machine"
    ROASTER = "roaster"
    GRINDER = "grinder"
    BREWER = "brewer"


# Expected useful life per category; the term rule forbids financing past it.
EQUIPMENT_LIFETIME_MONTHS: dict[EquipmentCategory, int] = {
    EquipmentCategory.ESPRESSO_MACHINE: 120,
    EquipmentCategory.ROASTER: 180,
    EquipmentCategory.GRINDER: 84,
    EquipmentCategory.BREWER: 60,
}


@dataclass(frozen=True)
class CafeProfile:
    name: str
    months_in_business: int
    monthly_revenue: Decimal
    seats: int
    has_existing_financing: bool


@dataclass(frozen=True)
class EquipmentItem:
    category: EquipmentCategory
    description: str
    price: Decimal

    @property
    def expected_lifetime_months(self) -> int:
        return EQUIPMENT_LIFETIME_MONTHS[self.category]


@dataclass(frozen=True)
class FinancingApplication:
    application_id: str
    cafe: CafeProfile
    equipment: EquipmentItem
    term_months: int
    down_payment: Decimal
    annual_rate: Decimal

    @property
    def financed_amount(self) -> Decimal:
        return self.equipment.price - self.down_payment
