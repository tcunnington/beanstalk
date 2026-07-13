"""Pydantic request/response models: the API's contract with partners.

Conversion to and from domain types happens here, so routes stay thin and
the domain stays pydantic-free.
"""

from decimal import Decimal

from pydantic import BaseModel, Field

from beanstalk.core.application import (
    CafeProfile,
    EquipmentCategory,
    EquipmentItem,
    FinancingApplication,
)
from beanstalk.core.decision import Decision


class CafePayload(BaseModel):
    name: str
    months_in_business: int = Field(ge=0)
    monthly_revenue: Decimal = Field(ge=0)
    seats: int = Field(ge=0)
    has_existing_financing: bool = False

    def to_domain(self) -> CafeProfile:
        return CafeProfile(
            name=self.name,
            months_in_business=self.months_in_business,
            monthly_revenue=self.monthly_revenue,
            seats=self.seats,
            has_existing_financing=self.has_existing_financing,
        )


class EquipmentPayload(BaseModel):
    category: EquipmentCategory
    description: str
    price: Decimal = Field(gt=0)

    def to_domain(self) -> EquipmentItem:
        return EquipmentItem(category=self.category, description=self.description, price=self.price)


class ApplicationRequest(BaseModel):
    cafe: CafePayload
    equipment: EquipmentPayload
    term_months: int = Field(gt=0)
    down_payment: Decimal = Field(ge=0)


class ReasonPayload(BaseModel):
    code: str
    message: str


class DecisionResponse(BaseModel):
    application_id: str
    outcome: str
    reasons: list[ReasonPayload]
    risk_score: float
    monthly_payment: Decimal

    @classmethod
    def from_domain(cls, decision: Decision) -> "DecisionResponse":
        return cls(
            application_id=decision.application_id,
            outcome=decision.outcome.value,
            reasons=[ReasonPayload(code=r.code, message=r.message) for r in decision.reasons],
            risk_score=decision.risk_score,
            monthly_payment=decision.monthly_payment,
        )


class ApplicationDetail(BaseModel):
    cafe_name: str
    equipment_description: str
    term_months: int
    financed_amount: Decimal
    decision: DecisionResponse

    @classmethod
    def from_domain(
        cls, application: FinancingApplication, decision: Decision
    ) -> "ApplicationDetail":
        return cls(
            cafe_name=application.cafe.name,
            equipment_description=application.equipment.description,
            term_months=application.term_months,
            financed_amount=application.financed_amount,
            decision=DecisionResponse.from_domain(decision),
        )
