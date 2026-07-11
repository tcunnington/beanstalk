"""Known-bad fixture: data models carrying business logic or touching I/O."""

import logging
from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel


@dataclass
class Order:
    quantities: list[int]
    unit_price: Decimal

    def settle(self) -> int:  # ARCH201: cognitive complexity above threshold
        outcome = 0
        for quantity in self.quantities:
            if quantity > 0:
                if self.unit_price > 100:
                    outcome += 2
                elif self.unit_price > 10:
                    outcome += 1
                else:
                    outcome -= 1
            else:
                outcome -= 2
        return outcome


class Invoice(BaseModel):
    number: str

    def send(self) -> None:  # ARCH202: a data model doing I/O
        logging.getLogger(__name__).info("sending invoice %s", self.number)
