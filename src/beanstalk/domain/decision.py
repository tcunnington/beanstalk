"""The outcome of decisioning a financing application.

A declined application is a normal business outcome, not an error — declines
are values (a Decision with reasons), never exceptions.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class DecisionOutcome(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class Reason:
    code: str
    message: str


@dataclass(frozen=True)
class Decision:
    application_id: str
    outcome: DecisionOutcome
    reasons: tuple[Reason, ...]
    risk_score: float
    monthly_payment: Decimal

    def summary(self) -> str:
        """One-line human-readable summary, e.g. for logs and list views."""
        codes = ", ".join(reason.code for reason in self.reasons) or "clean"
        return f"{self.outcome.value} (risk={self.risk_score:.2f}; {codes})"
