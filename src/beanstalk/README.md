# beanstalk (source root)

Four tiers, stacked by how fast their concepts change — each imports only from
below — plus independent **feature sandboxes** (tier 3) and **interfaces**
(delivery mechanisms). All of it is enforced by the import contracts in
`pyproject.toml` — `just imports` to verify, or `just graph` to see it.

| Package | Tier / kind | May import |
|---|---|---|
| [utils/](utils/README.md) | tier 1 | stdlib + pure third-party libs (no frameworks, no I/O) |
| [core/](core/README.md) | tier 2 | utils (same purity rule) |
| [features/](features/README.md) | tier 3 sandboxes | core, utils (+ any library inside the sandbox) |
| [services/](services/README.md) | tier 4 coordination | features, core, utils |
| [interfaces/api/](interfaces/api/README.md) | interface | services, core, utils — **not ui, not any feature** |
| [interfaces/ui/](interfaces/ui/README.md) | interface | services, core, utils — **not api, not any feature** |

[features/](features/README.md) holds one sandbox per product capability
(`risk_scorer`, `machine_recommender`); each exposes a single `entrypoint.py`
and never imports a sibling. [interfaces/](interfaces/README.md) holds every
delivery mechanism — HTTP APIs, server-rendered UIs, and stubs for the kinds a
larger app grows (Airflow DAGs, CLIs, workers); interfaces are thin: parse
input, call a service, format output.

The three import contracts:

1. **layers** — `interfaces (api | ui) → services → features → core → utils`; a
   lower tier never imports a higher one. Within a tier, `api | ui` and
   `risk_scorer | machine_recommender` are independent siblings.
2. **independence** — api, ui, and the two features never import each other.
   Interfaces reach features *only through services*, and features cooperate
   *only through services* (the services→features edges are `ignore_imports`-ed,
   so only direct imports break the contract).
3. **forbidden** — utils and core import no frameworks and do no I/O (pydantic,
   fastapi, sklearn, sqlite3, httpx are deny-listed). Pure third-party libraries
   are fine — the rule is purity, not zero dependencies. Feature sandboxes are
   exempt; they may use anything.

Rationale: [docs/design-rules.md](../../docs/design-rules.md), Part 2.
