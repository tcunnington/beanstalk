# utils/ — tier 1: utilities

**Velocity: never-changing.** Generic helpers with zero knowledge of coffee,
financing, or Beanstalk.

| Module | Provides |
|---|---|
| `money.py` | Decimal rounding (banker's) and `$1,234.56` formatting |
| `finmath.py` | amortized (annuity) monthly-payment math |
| `ids.py` | short random identifiers |

**What belongs here:** pure input→output functions any project could copy
verbatim. The test: could this file be open-sourced without leaking anything
about the business or the infrastructure?

**What must NOT be here:** business vocabulary (cafes, applications, decisions),
I/O, frameworks, state. Infra wrappers are `services/` adapters, however
generic they look — tier 1 is about *knowledge*, not reusability.

**Allowed imports:** stdlib and pure third-party libraries. Beanstalk happens to
need only stdlib here, but smoothing helpers over libs like toolz, Shapely, or
numpy belong in this tier too. The rule is "no frameworks, no I/O" (the
`forbidden` import contract's deny-list), not "no dependencies".

**Testing:** exhaustive unit tests, zero mocking (`tests/unit/`).
