"""Risk scoring: the seam between services and the model product."""

from typing import Protocol

from beanstalk.domain.application import FinancingApplication
from beanstalk.model.features import features_from_application
from beanstalk.model.predict import RiskModel


class RiskScorer(Protocol):
    """Anything that can put a default-risk number on an application."""

    def score(self, application: FinancingApplication) -> float: ...


class ModelRiskScorer:
    """Scores applications with the trained RiskModel artifact."""

    def __init__(self, risk_model: RiskModel) -> None:
        self._risk_model = risk_model

    def score(self, application: FinancingApplication) -> float:
        return self._risk_model.predict_default_risk(features_from_application(application))
