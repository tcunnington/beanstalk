"""The feature schema at the model boundary.

FeatureVector is the Pydantic contract every caller must satisfy;
FEATURE_COLUMNS fixes the column order of the training matrix.
"""

from pydantic import BaseModel, Field

from beanstalk.core.affordability import monthly_payment_for
from beanstalk.core.application import FinancingApplication

FEATURE_COLUMNS = (
    "months_in_business",
    "monthly_revenue",
    "seats",
    "has_existing_financing",
    "financed_amount",
    "payment_to_revenue",
)


class FeatureVector(BaseModel):
    months_in_business: int = Field(ge=0)
    monthly_revenue: float = Field(ge=0)
    seats: int = Field(ge=0)
    has_existing_financing: bool
    financed_amount: float = Field(ge=0)
    payment_to_revenue: float = Field(ge=0)

    def as_row(self) -> list[float]:
        """The vector in FEATURE_COLUMNS order, ready for the estimator."""
        return [float(getattr(self, column)) for column in FEATURE_COLUMNS]


def features_from_application(application: FinancingApplication) -> FeatureVector:
    """Project a domain application onto the model's feature space."""
    revenue = application.cafe.monthly_revenue
    payment = monthly_payment_for(application)
    # A cafe with no revenue maxes out the ratio; eligibility declines it anyway.
    payment_to_revenue = float(payment / revenue) if revenue > 0 else 1.0
    return FeatureVector(
        months_in_business=application.cafe.months_in_business,
        monthly_revenue=float(revenue),
        seats=application.cafe.seats,
        has_existing_financing=application.cafe.has_existing_financing,
        financed_amount=float(application.financed_amount),
        payment_to_revenue=payment_to_revenue,
    )
