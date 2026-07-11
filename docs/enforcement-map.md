# Enforcement map

Every rule in [design-rules.md](design-rules.md), mapped to the tool that enforces it.
The repo's meta-lesson: **push rules down this table** — a rule a machine enforces
needs no prose, no review comment, and no agent memory.

Legend: 🟢 machine-enforced (fails `just check`) · 🟡 partially enforced · ⚪ review-only

| Rule (design-rules.md) | Status | Enforced by |
|---|---|---|
| Tier layering: services → domain → utils | 🟢 | import-linter `layers` contract |
| Vertical modules (api, ui, model) independent | 🟢 | import-linter `independence` contract (+ `ignore_imports` for the services→model seam) |
| Tiers 1–2 framework-free (no pydantic/fastapi/sklearn/sqlite3) | 🟢 | import-linter `forbidden` contract |
| Anemic domain models (no business logic on data objects) | 🟢 | archcheck ARCH201 (cognitive complexity via complexipy) + ARCH202 (no I/O calls) — `tests/arch/test_model_logic.py` |
| Composition over inheritance | 🟢 | archcheck ARCH101 (base allow-list) + ARCH102 (no multiple inheritance) — `tests/arch/test_no_inheritance.py` |
| Duck typing / Protocols over ABCs | 🟢 | `abc.ABC` deliberately absent from the ARCH101 allow-list |
| One responsibility per class (cohesion) | 🟢 | archcheck ARCH301 (LCOM4 = 1) — `tests/arch/test_lcom4.py` |
| Pydantic only at boundaries; native types inside | 🟢 | `forbidden` contract + allow-list (BaseModel allowed, domain can't import it) |
| Max function length / branching | 🟢 | ruff PLR0915 (`max-statements = 60`), PLR0912 |
| ≤ 2–3 mandatory positional args; keyword-only config | 🟢 | ruff PLR0913 / PLR0917 (`max-positional-args = 3`, `max-args = 6`) |
| Immutability by default | 🟡 | convention (`frozen=True` everywhere in domain); pyright strict catches mutation of frozen dataclasses |
| Catch the narrowest exception; never bare `except:` | 🟡 | ruff E722 (bare except); breadth of `except Exception` is review-only |
| Never swallow silently | 🟡 | ruff SIM105 and B-series catch some forms |
| Chain exceptions with `from` | 🟢 | ruff B904 |
| Kill dead code / commented-out blocks | 🟡 | ruff ERA not enabled (noisy); review-only by default |
| Exceptions are not control flow (declines are values) | ⚪ | design: `Decision` with reasons is the return type; review-only |
| Explicit over implicit state; composition over DI frameworks | ⚪ | design: app factories + constructor args; review-only |
| No premature design patterns / hypothetical abstraction | ⚪ | review-only |
| Service-to-service chains | ⚪ | review-only (import-linter can't see call graphs) |
| Naming: intent, by domain, snake_case/CamelCase | 🟡 | ruff N-series not enabled; conventions review-only |
| Stepdown rule; `_helper` below caller; avoid nesting | ⚪ | review-only |
| Google-style docstrings on public modules | ⚪ | ruff D-series not enabled (noisy for a toy repo); review-only |
| Boy Scout rule | ⚪ | review-only |

## Where each config lives

- import-linter contracts: `pyproject.toml` → `[tool.importlinter]`
- archcheck thresholds and allow/deny lists: `pyproject.toml` → `[tool.archcheck]`
- ruff selection and pylint limits: `pyproject.toml` → `[tool.ruff]`
- pyright strictness per tier: `pyproject.toml` → `[tool.pyright]`

Run everything with `just check`.
