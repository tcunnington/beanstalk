# beanstalk (source root)

Six packages along two dimensions: **tiers** (how fast concepts change) and
**vertical modules** (independently deployable apps). Both are enforced by
import-linter contracts in `pyproject.toml` — `just imports` to verify.

| Package | Kind | May import |
|---|---|---|
| [utils/](utils/README.md) | tier 1 | stdlib only |
| [domain/](domain/README.md) | tier 2 | utils |
| [model/](model/README.md) | vertical (ML core) | domain, utils (+ pydantic/sklearn) |
| [services/](services/README.md) | tier 3 | model, domain, utils |
| [api/](api/README.md) | vertical app | services, domain, utils — **not ui, not model** |
| [ui/](ui/README.md) | vertical app | services, domain, utils — **not api, not model** |

The three contracts:

1. **layers** — `(api | ui) → services → model → domain → utils`; a lower layer never
   imports a higher one, and api/ui are independent siblings.
2. **independence** — api, ui, and model never import each other. api/ui reach the
   model *only through services* (the services→model edges are `ignore_imports`-ed,
   so only direct imports break the contract).
3. **forbidden** — utils and domain import no frameworks (pydantic, fastapi,
   sklearn, sqlite3, httpx). The pure core stays pure.

Rationale: [docs/design-rules.md](../../docs/design-rules.md), Part 2.
