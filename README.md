# Beanstalk

## What this is

This is a worked example of how I build software: code organized by how often
each part changes rather than by technical role, with the rules enforced by
machines instead of a wiki page nobody rereads. Import contracts, custom AST
checks, and a battery of architecture tests all fail the build the moment code
drifts from the shape it's supposed to have. If you want to lift the pattern
into your own repo instead of just reading about it, there's a mapping guide
for that: [docs/adopting-this.md](docs/adopting-this.md).

The app underneath is deliberately unremarkable. It exists to give the
architecture something real to hold up, not the other way around.

## The toolbox

| Concern | Tool |
|---|---|
| Layered architecture + module independence | import-linter — three contracts in `pyproject.toml` |
| Composition over inheritance, anemic data models, cohesion | custom AST checkers in [tests/arch/](tests/arch/README.md) |
| Validation at boundaries | Pydantic (api schemas, ui forms, feature inputs, settings) |
| Lint + format, including function-size and argument-count limits | ruff |
| Type checking | pyright (the gate) + [ty](https://github.com/astral-sh/ty) (informational) |
| Env + lockfile | uv |
| Dependency hygiene | deptry |
| Task running | just |
| Agent guidance | [CLAUDE.md](CLAUDE.md) → [docs/design-rules.md](docs/design-rules.md) + [docs/enforcement-map.md](docs/enforcement-map.md) |

I skip coverage gates, tox/nox, docker, and DI frameworks on purpose — they
weren't pulling their weight at this size, and I'd rather add them when they
start to hurt than defend them up front.

## The app

Cafés apply to finance espresso machines and roasters. Eligibility policy and
affordability math are plain rules; a small ML model estimates default risk;
together they produce an `APPROVED` / `DECLINED` / `NEEDS_REVIEW` decision,
with reasons attached. A human works the review queue through a
server-rendered UI.

It's deliberately not a hard problem — just enough logic to need the
layering, not so much that the business itself becomes the interesting part.

## Architecture

Four tiers stacked by velocity of change, plus independent feature sandboxes
and interfaces — all enforced by import contracts
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

Everything above is enough to run the app. Below is the reasoning, if you
want it.

### Layered by velocity of change

I organize code by **how often it changes**, not by its technical role, and
imports may only point toward the more stable end (`docs/design-rules.md`,
Part 2):

- **`utils` (tier 1)** is generic and domain-free: `monthly_payment()` would
  work at any lender. It essentially never changes, so everything may lean on it.
- **`core` (tier 2)** is the business itself — frozen dataclasses plus pure
  functions: eligibility rules, affordability caps, and `decide()`, which
  combines them with a risk score. Enterprise-wide truths, shared by every
  feature. No I/O, no frameworks. Changes only when the business does.
- **`features` (tier 3)** are sandboxed product capabilities — `risk_scorer`
  (the real sklearn model) and `machine_recommender` (a stub). This is where
  product work actually happens, so it's the **constantly-changing** tier: each
  is a mini-app that builds on core but is otherwise free to use any library and
  any internal layout. They never import each other.
- **`services` (tier 4)** is coordination: a thin broker that loads features,
  scores, decides, persists. It's **usually stable** — not because it's high in
  the stack, but *because* it's kept thin. A broker that stays a broker doesn't
  accumulate the churn its features go through; the moment it starts absorbing
  product logic, it stops being stable (see "Fat Services" in the red flags).

Layering does its job regardless of which tier moves fastest: nothing below a
tier may know it exists, so churn — wherever it concentrates — can't
propagate downward.

Two things sit *across* the tiers. Delivery mechanisms live under
`interfaces/` — the partner API, the reviewer UI, and a stub showing where an
Airflow DAG or CLI would go. Interfaces are thin edges: parse input, call a
service, format output; they relate to capabilities many-to-many *through
services*. And each feature is a sandbox reached through a single
`entrypoint.py`. Everything that must stay independent — api, ui, and the two
features — is mutually independent: the API doesn't know the UI exists,
neither may import a feature directly, and `risk_scorer` and
`machine_recommender` can't reach into each other. When the API needs a risk
score it goes through `services`, which reaches the feature through a
one-method `RiskScorer` Protocol stated in core terms. That seam is what
makes the system testable: integration tests swap in a `StubScorer` and never
load sklearn.

A useful frame: if these were microservices, each **feature** would be a
service and the **services tier** would be the message bus wiring them —
which is why features meet only there, never in a private back channel.

Who wires it all together? `build_application_service()` in
[services/applications.py](src/beanstalk/services/applications.py) — the
composition root. Plain constructor calls (settings → records store + feature
entrypoints → service), no DI framework.

### The clean-code rules that actually bite

[docs/design-rules.md](docs/design-rules.md) ("The Layered Pragmatist") is
the source of truth, loosely adapted from Robert C. Martin's *Clean Code*. A
few of its rules show up constantly in this codebase.

Data models stay anemic — dataclasses carry data, logic lives in core
functions or services. `Decision.summary()`, one line of formatting, is about
as far as a method on a data model is allowed to go.

The core layer has no behavior classes at all. The only classes that hold
behavior own real state: a sqlite connection (`DecisionRecordStore`, wrapping
the generic `SqliteAdapter`), a loaded model artifact (`RiskModel`).

`RiskScorer` is a `typing.Protocol`, not a base class — the feature's
entrypoint conforms to it structurally, inheriting nothing. `abc.ABC` is
deliberately left off the inheritance allow-list.

A declined application isn't an error, it's a normal outcome, so it comes
back as a value (`Decision`, with reasons) rather than an exception.
Exceptions are for the genuinely unexpected — `ApplicationNotFoundError`
becomes a 404, caught narrowly, chained with `raise ... from`.

Pydantic only shows up at the boundaries: API schemas, UI forms, feature
inputs, settings. Inside core it's plain frozen dataclasses, and that's not a
convention I have to remember — the import contracts make it a build failure
to violate. Feature sandboxes are exempt; inside a sandbox, anything goes.

Purity, to me, is about frameworks and I/O, not dependency count — utils and
core lean on pure third-party libraries like numpy freely. What the
`forbidden` contract actually bans is frameworks and anything that touches
the outside world. Infrastructure wrappers live in `services/adapters`,
never in `utils`, no matter how generic they look.

### Enforcement over documentation

A rule a tool enforces doesn't need prose, review vigilance, or a place in
anyone's memory. That's the whole strategy here — the import contracts and
arch checkers are the load-bearing part of the design; everything else is
commentary. The three import contracts (in `pyproject.toml`):

1. **layers** — the diagram above, literally: `interfaces (api | ui) →
   services → features → core → utils`. Any upward import fails with the
   exact chain.
2. **independence** — api, ui, and the two features may not import each
   other. Layering alone would still let the API `import
   beanstalk.features.risk_scorer` directly, and would let one feature import
   another; this contract forbids both, forcing every such link through the
   services seam. (Independence also counts *transitive* chains, so the
   legitimate `services → features` edges are `ignore_imports`-ed, leaving
   exactly the rule I want — no *direct* imports.)
3. **forbidden** — utils and core may not import pydantic, fastapi, sklearn,
   sqlite3… Tier purity, mechanically. (Features are exempt — they're
   sandboxes.)

Beyond imports, three custom AST checkers run as pytest
([tests/arch/](tests/arch/README.md)): **ARCH101/102** (inheritance
allow-list, no multiple inheritance), **ARCH201/202** (data-model methods
stay trivially simple — measured with complexipy — and never touch I/O),
**ARCH301** (LCOM4: a class whose methods form disconnected groups is really
several classes). Each checker is proven by fixtures: known-bad files that
are parsed, never imported, and must always fail — permanent negative proofs
that the checks still catch what they claim.

[docs/enforcement-map.md](docs/enforcement-map.md) closes the loop: every
rule in the design guide mapped to the tool that enforces it, or honestly
marked review-only.

### Where to dig in

| To understand… | Read |
|---|---|
| Package boundaries + the contract table | [src/beanstalk/README.md](src/beanstalk/README.md) |
| The full design rationale | [docs/design-rules.md](docs/design-rules.md) |
| Which tool enforces which rule | [docs/enforcement-map.md](docs/enforcement-map.md) |
| How the checkers work — and their blind spots | [tests/arch/README.md](tests/arch/README.md) |
| The business, end to end | [core/decisioning.py](src/beanstalk/core/decisioning.py), then [services/applications.py](src/beanstalk/services/applications.py) |
| A feature sandbox + its entrypoint | [features/README.md](src/beanstalk/features/README.md), then [features/risk_scorer/entrypoint.py](src/beanstalk/features/risk_scorer/entrypoint.py) |
| How to port this setup to a *different* app | [docs/adopting-this.md](docs/adopting-this.md) |

### Why this matters for agents too

I set up the context strategy the same way I'd budget a new hire's attention:
cheapest signal first. Machine enforcement catches most violations without
anyone reading a single doc — `just check` is the one gate, whether a human
or an agent is driving. [CLAUDE.md](CLAUDE.md) is next: short enough to read
in a minute, loaded automatically every session, with the architecture map, a
where-does-my-change-go table, and the golden rules, each linking to what
enforces it. Only past that does anyone need to open `docs/` and read the
actual reasoning.

Failures teach, too — every ARCH violation cites the exact design-rule
section it enforces, so the rationale resurfaces exactly when it's needed: at
the moment the rule breaks, which is also the moment an agent with compacted
context needs reminding most.
