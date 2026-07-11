# utils/ — tier 1: utilities

**Velocity: never-changing.** Generic helpers with zero knowledge of coffee,
financing, or Beanstalk.

| Module | Provides |
|---|---|
| `money.py` | Decimal rounding (banker's) and `$1,234.56` formatting |
| `finmath.py` | amortized (annuity) monthly-payment math |
| `ids.py` | short random identifiers |

**What belongs here:** pure input→output functions any project could copy verbatim.

**What must NOT be here:** business vocabulary (cafes, applications, decisions),
I/O, frameworks, state.

**Allowed imports:** stdlib only — enforced by the `layers` and `forbidden`
contracts (`just imports`).

**Testing:** exhaustive unit tests, zero mocking (`tests/unit/`).
