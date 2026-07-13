# services/ — tier 4: coordination

**Velocity: usually stable.** The broker: lightweight facades that manage
high-level flow and orchestrate *between* features. All I/O lives here or above.
If these were microservices, this tier would be the message bus. Stability is
earned, not assumed — a service that stays thin stays stable; one that
accumulates product logic starts changing as fast as the features it touches
(the "Fat Services" red flag in docs/design-rules.md).

| Module | Provides |
|---|---|
| `settings.py` | `Settings` (pydantic-settings, `BEANSTALK_*` env vars) |
| `decision_records.py` | `DecisionRecordStore` — persists (application, decision) pairs; `ApplicationNotFoundError` |
| `adapters/sqlite.py` | `SqliteAdapter` — generic table-shaped SQLite operations, no business vocabulary |
| `scoring.py` | `RiskScorer` Protocol — the seam to the `risk_scorer` feature |
| `recommending.py` | `Recommender` Protocol — the seam to the `machine_recommender` feature |
| `applications.py` | `ApplicationService` (submit → score → decide → persist, reviews, recommendations) and `build_application_service()`, the composition root |

**House style in action:**
- the coordination tier declares what it needs from a feature as a `Protocol`
  stated in **core terms** (`RiskScorer`, `Recommender`); each feature's
  `entrypoint.py` conforms structurally. Services import a feature's entrypoint
  *only at the composition root* — never its internals.
- classes only where there's real state (a connection); dependencies passed
  explicitly via keyword-only `__init__` args — no DI framework, no globals
- interfaces are `Protocol`s, never ABCs
- core objects are serialized with pydantic `TypeAdapter`s *here*, so core
  itself stays pydantic-free

**Adapters vs. stores — the split within this tier:**
`adapters/sqlite.py`'s `SqliteAdapter` is generic infrastructure: it knows
tables, columns, and rows, and nothing about "decisions" or "applications" — it
could be copied into another project unchanged. `decision_records.py`'s
`DecisionRecordStore` is the business-specific layer one step up: it owns the
`decisions` schema, translates core objects to/from JSON, and calls the
adapter for the actual SQL. That split is the general shape for infrastructure
in this tier — a generic `adapters/` wrapper underneath, a business-named store
or client on top that gives it meaning.

**What must NOT be here:** business rules (eligibility belongs in `core/`), a
feature's internal logic (belongs in that `features/` sandbox), HTTP handling
(belongs in `interfaces/`). A service that grows real product logic is a smell —
push it down.

**Allowed imports:** `features` (entrypoints only), `core`, `utils` — never
anything under `interfaces/`.

sqlite is a **placeholder**, not a design commitment — `adapters/sqlite.py` is
where any real database driver would be swapped in, and that's the general
rule: wrappers around infrastructure (databases, queues, blob stores, external
APIs) live at this tier as adapters, never in `utils/`.

**Testing:** exercised through the API/UI integration tests
(`tests/integration/`), with a stub scorer standing in for the risk_scorer feature.
