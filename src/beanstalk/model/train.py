"""Train the default-risk model on synthetic data and write the artifact."""

from pathlib import Path

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from beanstalk.model.predict import DEFAULT_ARTIFACT_PATH
from beanstalk.model.synthetic import generate_training_data


def train(
    artifact_path: Path = DEFAULT_ARTIFACT_PATH, *, n_samples: int = 2000, seed: int = 7
) -> Path:
    """Fit scaler + logistic regression and persist the pipeline."""
    features, default_labels = generate_training_data(n_samples, seed=seed)
    pipeline = make_pipeline(StandardScaler(), LogisticRegression())
    pipeline.fit(features, default_labels)
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, artifact_path)
    return artifact_path


def main() -> None:
    artifact_path = train()
    print(f"Wrote risk model to {artifact_path}")


if __name__ == "__main__":
    main()
