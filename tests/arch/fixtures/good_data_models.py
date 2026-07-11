"""Known-good fixture: anemic data models with only derived/formatting methods."""

from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel, field_validator


@dataclass(frozen=True)
class Receipt:
    total: Decimal

    @property
    def display_total(self) -> str:
        return f"${self.total:.2f}"

    def to_json(self) -> dict[str, str]:
        return {"total": str(self.total)}


class SignupPayload(BaseModel):
    email: str

    @field_validator("email")  # boundary parsing is exempt
    @classmethod
    def email_has_at_sign(cls, value: str) -> str:
        if "@" not in value:
            raise ValueError("not an email address")
        return value
