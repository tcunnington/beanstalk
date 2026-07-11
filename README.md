# Beanstalk ☕📈

**Equipment financing for indie coffee shops** — and a practice ground for tools that
enforce clean code and layered architecture.

Cafés apply to finance espresso machines and roasters. The system applies hard
eligibility policy and affordability math (pure domain logic), an ML default-risk
score (the core product), and produces **APPROVED / DECLINED / NEEDS_REVIEW**
decisions with reasons. Humans work the review queue in a server-rendered UI.

The app is deliberately just complex enough to exercise the tooling below — the
tooling is the point.

## Architecture

Two orthogonal dimensions, both enforced by [import-linter](https://import-linter.readthedocs.io/):

```
        api          ui           ← vertical apps (mutually independent)
          \         /
           services               ← tier 3: orchestration, persistence, model loading
          /    |
      model    |                  ← the ML core product (reachable only via services)
          \    |
           domain                 ← tier 2: frozen dataclasses + pure business rules
             |
           utils                  ← tier 1: generic, domain-free helpers
```

Every package has a README stating its purpose, tier, and allowed imports.
Start at [src/beanstalk/README.md](src/beanstalk/README.md).

## What's being practiced here

| Concern | Tool |
|---|---|
| Layered architecture + module independence | import-linter (3 contracts in `pyproject.toml`) |
| No-inheritance rule (allow-list), anemic data models, LCOM4 cohesion | custom AST checkers in [tests/arch/](tests/arch/README.md) |
| Validation at application boundaries | Pydantic (api schemas, ui forms, model features, settings) |
| Lint + format (incl. function-size/argument rules) | ruff |
| Type checking | pyright (gate) + [ty](https://github.com/astral-sh/ty) (informational comparison) |
| Env + lockfile | uv |
| Dependency hygiene | deptry |
| Task running | just |
| Agent guidance | [CLAUDE.md](CLAUDE.md) → [docs/design-rules.md](docs/design-rules.md) + [docs/enforcement-map.md](docs/enforcement-map.md) |

Deliberately skipped (pragmatism over purity): coverage gates, tox/nox, docker,
DI frameworks.

## Getting started

```sh
uv sync              # install everything
just check           # ruff + pyright + ty + import-linter + tests + deptry
just train           # (re)train the risk model artifact
just api             # partner API on :8000        (POST /applications)
just ui              # reviewer queue on :8001
```

Try it:

```sh
curl -s localhost:8000/applications -X POST -H 'content-type: application/json' -d '{
  "cafe": {"name": "Little Wolf", "months_in_business": 24,
            "monthly_revenue": "38000", "seats": 22, "has_existing_financing": false},
  "equipment": {"category": "espresso_machine",
                 "description": "Slayer Steam LP, 2 group", "price": "18500"},
  "term_months": 48, "down_payment": "3700"
}'
```

## Layout

```
src/beanstalk/     the app (six packages, one README each)
tests/unit/        pure domain/utils tests (zero mocking)
tests/integration/ API + UI flows via TestClient
tests/model/       model sanity (AUC on held-out synthetic data)
tests/arch/        custom architecture checkers + their fixture proofs
docs/              the design guide and its enforcement map
```
