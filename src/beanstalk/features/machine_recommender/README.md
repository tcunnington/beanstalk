# features/machine_recommender/ — tier 3 feature: equipment recommender

Suggests an espresso machine for a cafe — a second product capability, parallel
to `risk_scorer` and completely independent of it. **The logic is a deliberate
stub** (a hard-coded catalog and a seats-based heuristic); it exists to show the
shape of a feature sandbox, not to be a real recommender.

| Module | Provides | Visibility |
|---|---|---|
| `entrypoint.py` | `load_recommender()` + `CatalogRecommender.recommend(cafe) -> EquipmentItem` | **public** — the only thing services imports |
| `catalog.py` | `CATALOG` of `MachineOption`s to choose from | private to the feature |

**What this demonstrates:**
- a feature exposing its capability through one `entrypoint.py`, returning a
  **core** type (`EquipmentItem`) so no feature detail leaks upward
- **feature independence** — it shares nothing with `risk_scorer`; the
  `independence` contract forbids either from importing the other
- **internal structure by choice** — `catalog.py` is the feature's own private
  module; a bigger feature would grow more, however it liked

**How it's reached:** `ApplicationService.recommend_machine(application_id)`
(tier 4) looks up the stored applicant and delegates here. Two features
cooperating only ever meet at the services tier, never directly.

**Allowed imports:** `beanstalk.core`, `beanstalk.utils`, and anything a real
version would need. Never another feature; never `services` or `interfaces`.

**Testing:** `tests/features/test_recommender.py` (in isolation) and
`tests/integration/test_recommendation.py` (through the service facade).
