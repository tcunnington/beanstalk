# services/ — tier 3: services

**Velocity: constantly-changing.** Orchestration: the *when* and *why* of
financing operations. All I/O lives here or above.

| Module | Provides |
|---|---|
| `settings.py` | `Settings` (pydantic-settings, `BEANSTALK_*` env vars) |
| `repository.py` | `DecisionRepository` — sqlite persistence; `ApplicationNotFoundError` |
| `scoring.py` | `RiskScorer` Protocol + `ModelRiskScorer` (the seam to `model/`) |
| `applications.py` | `ApplicationService` (submit → score → decide → persist, review overrides) and `build_application_service()`, the composition root |

**House style in action:**
- classes only where there's real state (a connection, a loaded artifact);
  dependencies passed explicitly via `__init__` — no DI framework, no globals
- interfaces are `Protocol`s (`RiskScorer`), never ABCs
- domain objects are serialized with pydantic `TypeAdapter`s *here*, so the
  domain layer itself stays pydantic-free

**What must NOT be here:** business rules (what makes an application eligible
belongs in `domain/`), feature engineering (belongs in `model/`), HTTP handling
(belongs in `api/`/`ui/`).

**Allowed imports:** `model`, `domain`, `utils` — never `api` or `ui`.

**Testing:** exercised through the API/UI integration tests
(`tests/integration/`), with a stub scorer standing in for the model.
