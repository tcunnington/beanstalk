# core/ — tier 2: core domain

**Velocity: slowly-changing.** The pure, stable foundation of equipment
financing: enterprise-wide concepts as native types and pure functions. No I/O,
no frameworks, no pydantic. These are the truths every feature builds on.

| Module | Provides |
|---|---|
| `application.py` | data shapes: `CafeProfile`, `EquipmentItem`, `FinancingApplication` (frozen dataclasses), `EquipmentCategory` |
| `decision.py` | `Decision`, `DecisionOutcome`, `Reason` — a decline is a *value*, never an exception |
| `eligibility.py` | hard rules (min months in business, term ≤ equipment life, min down payment) |
| `affordability.py` | payment-to-revenue policy, built on `utils.finmath` |
| `decisioning.py` | `decide(application, *, risk_score) -> Decision` — combines everything |

**What belongs here:** data shapes (`@dataclass(frozen=True)`, `Enum`) and the pure
functions that manipulate them — concepts shared across *every* feature. Rules
take core objects, return core objects.

**What must NOT be here:**
- business logic on the data objects themselves — models stay **bare records**
  (derived properties and formatting only; enforced by ARCH201/ARCH202)
- pydantic/sqlite/fastapi/sklearn imports (enforced by the `forbidden` contract)
- **feature-specific logic** — if only one capability cares about it, it belongs
  in that feature, not in core
- orchestration ("first score, then persist") — that's `services/`

**Allowed imports:** `beanstalk.utils`, stdlib, and pure third-party libraries
(same policy as utils: the `forbidden` import contract bans frameworks and I/O,
not dependencies).

**Testing:** business rules against core data, no mocks (`tests/unit/`).
