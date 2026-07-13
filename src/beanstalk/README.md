# beanstalk (source root)

Packages along two dimensions: **tiers** (how fast concepts change) and
**vertical modules** (independent delivery mechanisms and the ML core). Both are
enforced by the import contracts in `pyproject.toml` — `just imports` to verify.

| Package | Kind | May import |
|---|---|---|
| [utils/](utils/README.md) | tier 1 | stdlib + pure third-party libs (no frameworks, no I/O) |
| [domain/](domain/README.md) | tier 2 | utils (same purity rule) |
| [model/](model/README.md) | vertical (ML core) | domain, utils (+ pydantic/sklearn) |
| [services/](services/README.md) | tier 3 | model, domain, utils |
| [interfaces/api/](interfaces/api/README.md) | interface vertical | services, domain, utils — **not ui, not model** |
| [interfaces/ui/](interfaces/ui/README.md) | interface vertical | services, domain, utils — **not api, not model** |

[interfaces/](interfaces/README.md) holds every delivery mechanism — HTTP APIs,
server-rendered UIs, and stubs for the kinds a larger app grows (Airflow DAGs,
CLIs, workers). Interfaces are thin: parse input, call a service, format output.

The three import contracts:

1. **layers** — `interfaces (api | ui) → services → model → domain → utils`; a
   lower layer never imports a higher one, and api/ui are independent siblings.
2. **independence** — api, ui, and model never import each other. Interfaces reach
   the model *only through services* (the services→model edges are
   `ignore_imports`-ed, so only direct imports break the contract).
3. **forbidden** — utils and domain import no frameworks and do no I/O (pydantic,
   fastapi, sklearn, sqlite3, httpx are deny-listed). Pure third-party libraries
   are fine — the rule is purity, not zero dependencies.

Rationale: [docs/design-rules.md](../../docs/design-rules.md), Part 2.
