# Beanstalk — agent rules

**The Creed: optimize for low cognitive overhead.** Complexity builds up linearly
through the tiers; any single function's novel contribution stays small and readable.

## Architecture (enforced by import-linter — you cannot break it silently)

```
api | ui          vertical apps (independent; reach the model only through services)
   └─ services    tier 3: orchestration, DB, model loading (constantly changing)
       └─ model   the ML core product
       └─ domain  tier 2: frozen dataclasses + pure functions (slowly changing)
           └─ utils  tier 1: generic, domain-free helpers (never changing)
```

## Golden rules

1. Data models are anemic: derived properties and formatting only. Logic lives in
   domain functions or services. (Enforced: ARCH201/ARCH202.)
2. Composition over inheritance. Inherit only from the allow-list in
   `[tool.archcheck]`; never multiple bases; Protocols, not ABCs. (ARCH101/102.)
3. Domain and utils are pure: no pydantic, no I/O, no frameworks. Pydantic models
   live only at boundaries (api schemas, ui forms, model features, settings).
4. Declines are values (`Decision` with reasons), never exceptions. Exceptions are
   for the unexpected only; catch narrowly; chain with `raise ... from`.
5. Prefer functions over classes; a class needs real state (connection, artifact).
   Pass dependencies explicitly through `__init__` — no DI frameworks, no globals.
6. Stepdown layout: orchestrator on top, `_helpers` directly below their caller.
7. Every package README states what belongs there — read it before adding files.

**Before you're done: `just check` must pass.** Full rationale in
[docs/design-rules.md](docs/design-rules.md); what enforces each rule in
[docs/enforcement-map.md](docs/enforcement-map.md).
