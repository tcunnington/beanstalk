# model/ — the ML core product

A default-risk model for financing applications: the thing Beanstalk actually
sells. A **vertical module**: independent of api/ui, sitting between services and
domain in the layer stack. Apps reach it *only through services*.

| Module | Provides |
|---|---|
| `features.py` | `FeatureVector` — the Pydantic contract at the model boundary — and `features_from_application()` |
| `synthetic.py` | synthetic cafés + default labels (hidden linear rule + noise) |
| `train.py` | fit scaler + logistic regression, write the artifact (`just train`) |
| `predict.py` | `RiskModel.load().predict_default_risk(features) -> float` |
| `artifacts/` | the trained artifact, committed for reproducibility |

**What belongs here:** feature engineering, training, inference, model artifacts.

**What must NOT be here:** HTTP anything, persistence of applications, decision
policy (thresholds live in domain/services — the model only produces a score).

**Allowed imports:** `beanstalk.domain`, `beanstalk.utils`, sklearn/numpy/pydantic.
Enforced: never imports `services` or anything under `interfaces/`.

sklearn is a **placeholder**, not a design commitment — any inference stack
(xgboost, torch, an external endpoint) slots in behind `RiskModel` unchanged.

**Testing:** `tests/model/` — AUC above chance on held-out synthetic data.
