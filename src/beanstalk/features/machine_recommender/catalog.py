"""The equipment catalog the recommender chooses from — a stand-in for a real one.

Feature-private data: it lives inside the sandbox and speaks Core vocabulary
(`EquipmentCategory`), but nothing outside the feature imports it.
"""

from dataclasses import dataclass
from decimal import Decimal

from beanstalk.core.application import EquipmentCategory


@dataclass(frozen=True)
class MachineOption:
    category: EquipmentCategory
    model_name: str
    price: Decimal
    min_seats: int
    blurb: str


# Ordered small -> large; the recommender picks the biggest a cafe can seat.
CATALOG: tuple[MachineOption, ...] = (
    MachineOption(
        category=EquipmentCategory.ESPRESSO_MACHINE,
        model_name="Rancilio Silvia Pro X",
        price=Decimal("3200"),
        min_seats=0,
        blurb="single group for a small counter",
    ),
    MachineOption(
        category=EquipmentCategory.ESPRESSO_MACHINE,
        model_name="La Marzocco Linea Mini",
        price=Decimal("6500"),
        min_seats=12,
        blurb="sized for a neighborhood cafe",
    ),
    MachineOption(
        category=EquipmentCategory.ESPRESSO_MACHINE,
        model_name="La Marzocco Linea PB, 2 group",
        price=Decimal("18500"),
        min_seats=24,
        blurb="two groups for a steady rush",
    ),
    MachineOption(
        category=EquipmentCategory.ESPRESSO_MACHINE,
        model_name="Slayer Espresso, 3 group",
        price=Decimal("34000"),
        min_seats=48,
        blurb="three groups for high-volume service",
    ),
)
