# Beanstalk — agent rules

**The Creed: optimize for low cognitive overhead.** Complexity builds up linearly
through the tiers; any single function's novel contribution stays small and readable.

## Architecture (enforced by import contracts — you cannot break it silently)

```
interfaces/       delivery mechanisms: api | ui | (airflow stub) — independent,
   │              thin, reach the model only through services
   └─ services    tier 3: orchestration, DB, infra adapters (constantly changing)
       └─ model   the ML core product
       └─ domain  tier 2: frozen dataclasses + pure functions (slowly changing)
           └─ utils  tier 1: generic, domain-free helpers (never changing)
```

The import contracts and arch checks are the load-bearing implementation of the
design ethos — everything else in this file is commentary on them.

## Where does my change go?

| You're adding… | It belongs in |
|---|---|
| a business rule or policy threshold | `domain/` — pure functions (follow `eligibility.py`) |
| an API endpoint | `interfaces/api/routes.py` + a schema in `interfaces/api/schemas.py` |
| a UI page or form | `interfaces/ui/` (routes, forms, templates) |
| a new delivery mechanism (CLI, DAG, worker) | new subpackage under `interfaces/` |
| orchestration, persistence, an infra adapter | `services/` |
| a model feature | `model/features.py`, then retrain: `just train` |
| a generic, domain-free helper (pure 3rd-party libs OK) | `utils/` |

## Golden rules

1. Data models are anemic: derived properties and formatting only. Logic lives in
   domain functions or services. (Enforced: ARCH201/ARCH202.)
2. Composition over inheritance. Inherit only from the allow-list in
   `[tool.archcheck]`; never multiple bases; Protocols, not ABCs. (ARCH101/102.)
3. Domain and utils are pure: no pydantic, no I/O, no frameworks — but pure
   third-party libs (numpy-grade) are fine. Pydantic models live only at
   boundaries (api schemas, ui forms, model features, settings).
4. Declines are values (`Decision` with reasons), never exceptions. Exceptions are
   for the unexpected only; catch narrowly; chain with `raise ... from`.
5. Prefer functions over classes; a class needs real state (connection, artifact).
   Pass dependencies explicitly through `__init__` — no DI frameworks, no globals.
6. Stepdown layout: orchestrator on top, `_helpers` directly below their caller.
7. Before creating or moving any file: read that package's README. It states what
   belongs there and what must not.
8. Run servers through the `.claude/launch.json` preview configs (or `just api` /
   `just ui` in a terminal) — never ad-hoc background uvicorn.

**Before you're done: `just check` must pass.** Full rationale in
[docs/design-rules.md](docs/design-rules.md); what enforces each rule in
[docs/enforcement-map.md](docs/enforcement-map.md).
