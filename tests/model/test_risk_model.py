from pathlib import Path

import pytest
from sklearn.metrics import roc_auc_score

from beanstalk.model.features import FEATURE_COLUMNS, FeatureVector, features_from_application
from beanstalk.model.predict import ModelArtifactMissingError, RiskModel
from beanstalk.model.synthetic import generate_training_data
from beanstalk.model.train import train
from tests.unit.builders import healthy_application


def test_trained_model_beats_chance_on_held_out_data(tmp_path: Path):
    artifact_path = train(tmp_path / "risk.joblib", n_samples=2000, seed=7)
    model = RiskModel.load(artifact_path)

    held_out_features, held_out_labels = generate_training_data(250, seed=99)
    scores = [model.predict_default_risk(_vector_from_row(row)) for row in held_out_features]
    auc = roc_auc_score(held_out_labels, scores)
    assert auc > 0.7, f"AUC {auc:.3f} is barely better than chance"


def test_missing_artifact_raises_domain_error(tmp_path: Path):
    with pytest.raises(ModelArtifactMissingError, match="just train"):
        RiskModel.load(tmp_path / "nope.joblib")


def test_features_from_application_projects_domain_fields():
    features = features_from_application(healthy_application())
    assert features.months_in_business == 36
    assert features.financed_amount == 9600.0
    assert 0 < features.payment_to_revenue < 0.05


def _vector_from_row(row) -> FeatureVector:
    values = dict(zip(FEATURE_COLUMNS, row, strict=True))
    values["months_in_business"] = int(values["months_in_business"])
    values["seats"] = int(values["seats"])
    values["has_existing_financing"] = bool(values["has_existing_financing"])
    return FeatureVector(**values)
