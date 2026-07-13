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

Four tiers stacked by velocity of change, plus independent feature sandboxes and
interfaces — all enforced by import contracts
([import-linter](https://import-linter.readthedocs.io/)):

```
   interfaces/                       ← delivery mechanisms (mutually independent)
     api  ui  (airflow stub)
          \  /
        services                     ← tier 4: coordination/facades; owns infra
          /   \
   features/   \                     ← tier 3: sandboxed capabilities, each behind
  risk_scorer   \                      one entrypoint.py; never import each other
  machine_recommender
          \     |
           core                      ← tier 2: frozen dataclasses + pure rules
             |
           utils                     ← tier 1: generic, domain-free helpers
```

Each tier imports only from below. Every package has a README stating its
purpose, tier, and allowed imports — start at
[src/beanstalk/README.md](src/beanstalk/README.md), or run `just graph` to see
the real import graph.

## What's being practiced here

| Concern | Tool |
|---|---|
| Layered architecture + module independence | 3 import contracts in `pyproject.toml` (import-linter) |
| No-inheritance rule (allow-list), anemic data models, LCOM4 cohesion | custom AST checkers in [tests/arch/](tests/arch/README.md) |
| Validation at application boundaries | Pydantic (api schemas, ui forms, feature inputs, settings) |
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
src/beanstalk/     the app (tiers + features/ + interfaces/, one README per package)
tests/unit/        pure core/utils tests (zero mocking)
tests/features/    each feature in isolation (risk_scorer AUC, recommender)
tests/integration/ API + UI + coordination flows via TestClient
tests/arch/        custom architecture checkers + their fixture proofs
docs/              the design guide and its enforcement map
```

---

## Going deeper

Everything above tells you how to *run* the repo. This section teaches *why it
is shaped this way* — read it and every file placement and failing check below
should feel predictable rather than arbitrary.

### The structure: layered by velocity of change

The organizing idea (docs/design-rules.md, Part 2) is that code is layered by
**how often it changes**, and imports may only point toward the stable end:

- **`utils` (tier 1)** is generic and domain-free: `monthly_payment()` would
  work at any lender. It essentially never changes, so everything may lean on it.
- **`core` (tier 2)** is the business itself — frozen dataclasses plus pure
  functions: eligibility rules, affordability caps, and `decide()`, which
  combines them with a risk score. Enterprise-wide truths, shared by every
  feature. No I/O, no frameworks. Changes only when the business does.
- **`features` (tier 3)** are sandboxed product capabilities — `risk_scorer`
  (the real sklearn model) and `machine_recommender` (a stub). Each is a
  volatile mini-app that builds on core but is otherwise free to use any library
  and any internal layout. They never import each other.
- **`services` (tier 4)** is coordination: a thin broker that loads features,
  scores, decides, persists. It changes constantly — which is exactly why
  nothing below it may know it exists. Churn cannot propagate downward.

Two things sit *across* the tiers. Delivery mechanisms live under `interfaces/`
— the partner API, the reviewer UI, and a stub showing where an Airflow DAG or
CLI would go. Interfaces are thin edges: parse input, call a service, format
output; they relate to capabilities many-to-many *through services*. And each
feature is a sandbox reached through a single `entrypoint.py`. Everything that
must stay independent — api, ui, and the two features — is mutually independent:
the API doesn't know the UI exists, neither may import a feature directly, and
`risk_scorer` and `machine_recommender` can't reach into each other. When the
API needs a risk score it goes through `services`, which reaches the feature
through a one-method `RiskScorer` Protocol stated in core terms. That seam is
what makes the system testable: integration tests swap in a `StubScorer` and
never load sklearn.

A useful frame: if these were microservices, each **feature** would be a service
and the **services tier** would be the message bus wiring them — which is why
features meet only there, never in a private back channel.

Who wires it all together? `build_application_service()` in
[services/applications.py](src/beanstalk/services/applications.py) — the
composition root. Plain constructor calls (settings → repository + feature
entrypoints → service), no DI framework.

### The design principles the code actually follows

The house guide, [docs/design-rules.md](docs/design-rules.md) ("The Layered
Pragmatist"), is authoritative. The load-bearing rules as applied here:

- **Anemic data models.** Dataclasses carry data; logic lives in core
  functions or services. `Decision.summary()` — one line of formatting — is
  about the ceiling of what a method on a data model may do.
- **Functions over classes.** The core layer has zero behavior classes. The
  only classes with behavior hold *real state*: a sqlite connection
  (`DecisionRepository`), a loaded artifact (`RiskModel`).
- **Protocols, not ABCs.** `RiskScorer` is a `typing.Protocol`; the feature's
  entrypoint conforms structurally, inheriting nothing. `abc.ABC` is
  deliberately banned from the inheritance allow-list.
- **Declines are values.** A declined application is a normal business
  outcome, so it's a return value (`Decision` with reasons) — never an
  exception. Exceptions mark the genuinely unexpected
  (`ApplicationNotFoundError` → 404), caught narrowly, chained with
  `raise ... from`.
- **Pydantic at boundaries only.** Validation happens where untrusted data
  enters: API schemas, UI forms, feature inputs, settings. Inside core,
  everything is plain frozen dataclasses — and the import contracts make that
  mechanical fact, not convention. (Feature sandboxes are free to use pydantic
  or anything else internally.)
- **Purity is about frameworks and I/O, not dependencies.** utils and core
  may lean on pure third-party libraries (numpy-grade); what the `forbidden`
  contract bans is frameworks and anything that touches the world. Wrappers
  around infrastructure are `services/` adapters, never utils, however generic
  they look. Features are the exception — inside a sandbox, anything goes.

### The machine checks: enforce > document

A rule that a tool enforces needs no prose, no review vigilance, and no space
in anyone's memory. The import contracts and arch checkers are the load-bearing
implementation of the design ethos — everything else is commentary. The three
import contracts (in `pyproject.toml`):

1. **layers** — the diagram above, literally: `interfaces (api | ui) → services
   → features → core → utils`. Any upward import fails with the exact chain.
2. **independence** — api, ui, and the two features may not import each other.
   Layering alone would still let the API `import beanstalk.features.risk_scorer`
   directly, and would let one feature import another; this contract forbids
   both, forcing every such link through the services seam. (Subtlety:
   independence counts *transitive* chains too, so the legitimate
   `services → features` edges are `ignore_imports`-ed, leaving exactly the rule
   we want — no *direct* imports.)
3. **forbidden** — utils and core may not import pydantic, fastapi, sklearn,
   sqlite3… Tier purity, mechanically. (Features are exempt — they're sandboxes.)

Beyond imports, three custom AST checkers run as pytest ([tests/arch/](tests/arch/README.md)):
**ARCH101/102** (inheritance allow-list, no multiple inheritance),
**ARCH201/202** (data-model methods stay trivially simple — measured with
complexipy — and never touch I/O), **ARCH301** (LCOM4: a class whose methods
form disconnected groups is really several classes). Each checker is proven by
fixtures: known-bad files that are parsed, never imported, and must always
fail — permanent negative proofs that the checks still catch what they claim.

[docs/enforcement-map.md](docs/enforcement-map.md) closes the loop: every rule
in the design guide mapped to the tool that enforces it, or honestly marked
review-only.

### Working with agents

The context strategy is a funnel, cheapest first:

1. **Machine enforcement** (most rules) — needs zero context. An agent that
   never reads a single doc still can't ship an architecture violation;
   `just check` is the one gate, for humans and agents alike.
2. **[CLAUDE.md](CLAUDE.md)** (~45 lines, auto-loaded every session) — the
   architecture map, a where-does-my-change-go routing table, and the golden
   rules, each linking to its enforcer.
3. **docs/ on demand** — the full guide and enforcement map, read only when
   the reasoning matters.

And failures teach: every ARCH violation cites the design-rule section it
enforces, so the rationale resurfaces at exactly the moment the rule is
broken — which is also when an agent with compacted context needs it most.

### Where to dig in

| To understand… | Read |
|---|---|
| Package boundaries + the contract table | [src/beanstalk/README.md](src/beanstalk/README.md) |
| The full design rationale | [docs/design-rules.md](docs/design-rules.md) |
| Which tool enforces which rule | [docs/enforcement-map.md](docs/enforcement-map.md) |
| How the checkers work — and their blind spots | [tests/arch/README.md](tests/arch/README.md) |
| The business, end to end | [core/decisioning.py](src/beanstalk/core/decisioning.py), then [services/applications.py](src/beanstalk/services/applications.py) |
| A feature sandbox + its entrypoint | [features/README.md](src/beanstalk/features/README.md), then [features/risk_scorer/entrypoint.py](src/beanstalk/features/risk_scorer/entrypoint.py) |
