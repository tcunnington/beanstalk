# Beanstalk — agent rules

**The Creed: optimize for low cognitive overhead.** Complexity builds up linearly
through the tiers; any single function's novel contribution stays small and readable.

## Architecture (enforced by import contracts — you cannot break it silently)

```
interfaces/       delivery mechanisms: api | ui | (airflow stub) — independent,
   │              thin, reach features only through services
   └─ services    tier 4: coordination/facades; orchestrates features; owns infra
       │          (DB, settings) via adapters/. Usually stable.
       └─ features tier 3: sandboxed product capabilities, each behind one
          │        entrypoint.py (risk_scorer | machine_recommender). Never
          │        import each other; free to use any library/layout inside.
          │        Constantly changing — this is where product work happens.
          └─ core  tier 2: frozen dataclasses + pure functions (slowly changing)
              └─ utils  tier 1: generic, domain-free helpers (never changing)
```

The import contracts and arch checks are the load-bearing implementation of the
design ethos — everything else in this file is commentary on them.

## Where does my change go?

| You're adding… | It belongs in |
|---|---|
| an enterprise-wide rule or policy threshold | `core/` — pure functions (follow `eligibility.py`) |
| a new product capability (an engine, a model) | a new sandbox under `features/`, behind its own `entrypoint.py` |
| logic inside an existing capability | that feature's package (e.g. `features/risk_scorer/`) |
| an API endpoint | `interfaces/api/routes.py` + a schema in `interfaces/api/schemas.py` |
| a UI page or form | `interfaces/ui/` (routes, forms, templates) |
| a new delivery mechanism (CLI, DAG, worker) | new subpackage under `interfaces/` |
| coordination between features, persistence, config | `services/` |
| a generic, domain-free helper (pure 3rd-party libs OK) | `utils/` |

## Golden rules

1. Data models are bare records: derived properties and formatting only. Logic lives in
   core functions or services. (Enforced: ARCH201/ARCH202.)
2. Composition over inheritance. Inherit only from the allow-list in
   `[tool.archcheck]`; never multiple bases; Protocols, not ABCs. (ARCH101/102.)
3. Core and utils are pure: no pydantic, no I/O, no frameworks — but pure
   third-party libs (numpy-grade) are fine. Feature sandboxes may use anything;
   Pydantic lives at boundaries (api schemas, ui forms, feature inputs, settings).
   A feature is reached only through its `entrypoint.py`, which speaks core types.
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
