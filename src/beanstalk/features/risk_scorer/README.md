# features/risk_scorer/ — tier 3 feature: default-risk model

A default-risk model for financing applications — the capability Beanstalk
actually sells. A **feature sandbox**: independent of every other feature,
reached by the coordination tier *only through* `entrypoint.py`.

| Module | Provides | Visibility |
|---|---|---|
| `entrypoint.py` | `load_scorer()` + `ModelRiskScorer.score(application) -> float` | **public** — the only thing services imports |
| `feature_vector.py` | `FeatureVector` (Pydantic boundary) + `features_from_application()` | private to the feature |
| `synthetic.py` | synthetic cafés + default labels (hidden linear rule + noise) | private |
| `train.py` | fit scaler + logistic regression, write the artifact (`just train`) | private (CLI) |
| `predict.py` | `RiskModel.load().predict_default_risk(features) -> float` | private |
| `artifacts/` | the trained artifact, committed for reproducibility | private |

**What belongs here:** everything about turning an application into a risk
number — feature engineering, training, inference, artifacts, and the entrypoint
that wraps it all.

**What must NOT be here:** HTTP anything, persistence of applications, decision
policy (thresholds live in core/services — the model only produces a score), or
imports of another feature.

**Allowed imports:** `beanstalk.core`, `beanstalk.utils`, and the sandbox's own
stack (sklearn/numpy/pydantic/joblib). Enforced: never imports `services`,
`interfaces`, or a sibling feature.

sklearn is a **placeholder**, not a design commitment — any inference stack
(xgboost, torch, an external endpoint) slots in behind `entrypoint.py`
unchanged, and nothing outside the feature would notice.

**Testing:** `tests/features/test_risk_model.py` — AUC above chance on held-out
synthetic data, plus the feature-vector projection.
