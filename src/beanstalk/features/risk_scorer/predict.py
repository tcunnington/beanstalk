"""Load the trained artifact and score default risk for one application."""

from pathlib import Path

import joblib
import numpy as np

from beanstalk.features.risk_scorer.feature_vector import FeatureVector

DEFAULT_ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "default_risk.joblib"


class ModelArtifactMissingError(Exception):
    """The trained model artifact is not on disk."""


class RiskModel:
    """A trained default-risk estimator; state is the loaded sklearn pipeline."""

    def __init__(self, pipeline) -> None:
        self._pipeline = pipeline

    @classmethod
    def load(cls, artifact_path: Path = DEFAULT_ARTIFACT_PATH) -> "RiskModel":
        try:
            pipeline = joblib.load(artifact_path)
        except FileNotFoundError as err:
            raise ModelArtifactMissingError(
                f"No model artifact at {artifact_path}; run `just train` first."
            ) from err
        return cls(pipeline)

    def predict_default_risk(self, features: FeatureVector) -> float:
        """Probability of default in [0, 1] for a single feature vector."""
        row = np.array([features.as_row()])
        return float(self._pipeline.predict_proba(row)[0, 1])
