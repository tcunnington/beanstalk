# domain/ — tier 2: domain logic

**Velocity: slowly-changing.** The core business concepts of equipment financing,
as native types and pure functions. No I/O, no frameworks, no pydantic.

| Module | Provides |
|---|---|
| `application.py` | data shapes: `CafeProfile`, `EquipmentItem`, `FinancingApplication` (frozen dataclasses), `EquipmentCategory` |
| `decision.py` | `Decision`, `DecisionOutcome`, `Reason` — a decline is a *value*, never an exception |
| `eligibility.py` | hard rules (min months in business, term ≤ equipment life, min down payment) |
| `affordability.py` | payment-to-revenue policy, built on `utils.finmath` |
| `decisioning.py` | `decide(application, *, risk_score) -> Decision` — combines everything |

**What belongs here:** data shapes (`@dataclass(frozen=True)`, `Enum`) and the pure
functions that manipulate them. Rules take domain objects, return domain objects.

**What must NOT be here:**
- business logic on the data objects themselves — models stay **anemic**
  (derived properties and formatting only; enforced by ARCH201/ARCH202)
- pydantic/sqlite/fastapi/sklearn imports (enforced by the `forbidden` contract)
- orchestration ("first score, then persist") — that's `services/`

**Allowed imports:** `beanstalk.utils`, stdlib.

**Testing:** business rules against domain data, no mocks (`tests/unit/`).
