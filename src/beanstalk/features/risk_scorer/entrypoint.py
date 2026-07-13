"""The risk_scorer feature's single entry point.

The coordination tier reaches this feature only through here: `load_scorer()`
builds a scorer from the trained artifact, and the returned object satisfies
the `RiskScorer` protocol (score an application -> default risk in [0, 1]).
Everything else in this package is private to the feature.
"""

from pathlib import Path

from beanstalk.core.application import FinancingApplication
from beanstalk.features.risk_scorer.feature_vector import features_from_application
from beanstalk.features.risk_scorer.predict import DEFAULT_ARTIFACT_PATH, RiskModel


def load_scorer(artifact_path: Path | None = None) -> "ModelRiskScorer":
    """Load the trained artifact and wrap it as a scorer (feature default if None)."""
    return ModelRiskScorer(RiskModel.load(artifact_path or DEFAULT_ARTIFACT_PATH))


class ModelRiskScorer:
    """Scores applications with the trained RiskModel artifact."""

    def __init__(self, risk_model: RiskModel) -> None:
        self._risk_model = risk_model

    def score(self, application: FinancingApplication) -> float:
        return self._risk_model.predict_default_risk(features_from_application(application))
