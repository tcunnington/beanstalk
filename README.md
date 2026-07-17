# Beanstalk

## What it is

This is a worked example of how I would ideally build software: code organized in an
opinionated fashion, according to patterns of architecture and design that I've seen
work well in over a decade as an engineer and data scientist.
These patterns are designed to keep code clean, maintainable, scalable, and readable by both humans and AI.
The app underneath is deliberately unremarkable.
It exists to give the architecture something real to bite into, and to share the concepts.

Additionally, this repo takes the extra step of implementing automated checks.
These let machines check their own work as they write code, and fail the build whenever the code drifts from its intended shape.

If you want to lift the pattern into your own repo, there's a mapping guide at [docs/adopting-this.md](docs/adopting-this.md).

## The toolbox

| Concern | Tool |
|---|---|
| Layered architecture + module independence | import-linter — four contracts in `pyproject.toml` |
| Composition over inheritance, bare records, cohesion | custom AST checkers in [tests/arch/](tests/arch/README.md) |
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

Generally, the code is organized to support both horizontal and vertical concerns: first
by a four-tier structure, and second by independent verticals that each map to
a single technical function (and often to a single engineering team).

The four tiers are stacked by velocity of change.
The verticals are the independent feature sandboxes and the interfaces.
Interfaces are not included in the tiers, because some projects may not have them (a bare API can be absorbed into the service layer).
These are all enforced by import contracts
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
[src/beanstalk/README.md](src/beanstalk/README.md) to explore, or run `just graph` to see
the real import graph.

## Getting started

```sh
uv sync              # install everything
just check           # ruff + pyright + ty + import-linter + tests + deptry
just train           # (re)train the risk model artifact
just api             # partner API on :8000        (POST /applications)
just ui              # reviewer queue on :8001
```

Try hitting the API directly:

```sh
curl -s localhost:8000/applications -X POST -H 'content-type: application/json' -d '{
  "cafe": {"name": "Little Wolf", "months_in_business": 24,
            "monthly_revenue": "38000", "seats": 22, "has_existing_financing": false},
  "equipment": {"category": "espresso_machine",
                 "description": "Slayer Steam LP, 2 group", "price": "18500"},
  "term_months": 48, "down_payment": "3700"
}'
```

Or use the built-in scripts:
```
just try-api list_applications
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

Everything above is enough to run the app.
Below is more detail on the specific design choices made.

### Layered by velocity of change

I organize code primarily by **how pure it is** and **how often it changes**, and secondarily by product function.
Practically, this means splitting code so that imports stay simple: first by ensuring imports only point toward more stable code, according to "tiers"; and second by ensuring independence where it matters most.
There are four tiers of code: the first three go from more pure and slowly changing to more
domain-specific and quickly changing, while the final tier is essentially a thin facade tying it all together and interfacing with the external world (`docs/design-rules.md`, Part 2):

- **`utils` (tier 1)** is generic and domain-free: e.g. `monthly_payment()` would
  work at any lender. It essentially never changes, so everything may lean on it.
  These are also dead easy to test, having few or no dependencies and being pure functions.
- **`core` (tier 2)** is the most basic building blocks of the business. These are
  comprised of immutable (frozen) dataclasses, plus pure functions: eligibility rules,
  affordability caps, and `decide()`, which combines them with a risk score.
  These are enterprise-wide truths which may be shared by every feature. No I/O or end-to-end frameworks.
  Changes only when the business does.
- **`features` (tier 3)** are vertical product capabilities — `risk_scorer`
  (a sklearn model) and `machine_recommender` (a stub for another ML model). This is where
  product work actually happens, so it's the **constantly-changing** tier: each
  is a sandbox/mini-app that builds on core but is otherwise free to use any library and
  any internal layout within reason. They can never import each other and are ideally reached through a single `entrypoint.py`.
- **`services` (tier 4)** is coordination: a thin broker that loads features,
  scores, decides, persists. It's **usually stable**, but this is because it's kept *thin*,
  not because it's high in the stack. A broker that stays a broker doesn't
  accumulate the churn its features go through — and when it starts absorbing
  product logic, it stops being stable (see "Fat Services" in the red flags). _A callout_:
  right now all I/O sits under this tier, in `services/adapters`. This is due
  to the small scale; in reality, adapters would be used in tier 3 as well.

Layering means nothing below a tier may know it exists, so churn — wherever it concentrates — can't
propagate downward.

**Interfaces**

The delivery mechanisms at `interfaces/` live outside the four tiers by convention.
These can vary a lot in practice, but here there are three example interfaces: the partner API, the reviewer UI, and a stub showing where an Airflow DAG or CLI would go.
They relate to capabilities many-to-many *through services*.
They are mutually independent and cannot interact.

**Example of unidirectional information flow:**

When the API needs a risk score it goes through `services`, which reaches the feature through a
one-method `RiskScorer` Protocol stated in core terms.
The service uses `features.risk_scorer.entrypoint` to get a scorer, and the feature uses whatever it needs from `core` and `utils`.
Plus, that makes the system testable: integration tests swap in a `StubScorer` and never load sklearn.

**What if a feature needs to rely on another feature?**

A useful metaphor to consider: if these were microservices, each *feature* would be a
"service" and the *services tier* would be the message bus wiring them (and is why features
only ever meet there). What would you do in this paradigm?

**What wires it all together?**

`build_application_service()` in [services/applications.py](src/beanstalk/services/applications.py) does —
it's the composition root. A simple class interface with composition (settings → records store + feature
entrypoints → service).

### Design nitty gritty and clean-code rules

[docs/design-rules.md](docs/design-rules.md) ("Naos") is
the source of truth. It contains a mildly novel architecture & design guide in Part 2,
and a Part 3 loosely adapted from my memory of Robert C. Martin's *Clean Code*.
Below are the most important rules, which I'll admit come from a dedication to Python in this repo, and a general dislike of the over-application of OOP principles.

* Data models are plain dataclasses, while logic lives in core
functions or services. `Decision.summary()`, one line of formatting, is about
as far as a method on a data model is allowed to go. Keeping data and behavior
apart like this is normal in functional programming.

* Functions/modules are preferred over classes. The core layer has no behavior classes at all.
The only classes that hold behavior own real state: a sqlite connection (`DecisionRecordStore`,
a wrapper over the generic `SqliteAdapter`), a loaded model artifact (`RiskModel`).

* Protocols over abstract classes. `RiskScorer` is a `typing.Protocol`, not a base class — the feature's
entrypoint conforms to it structurally, inheriting nothing. `abc.ABC` is
deliberately left off the inheritance allow-list.

* Pydantic shows up at the boundaries where we need contracts: API schemas, UI forms, feature
inputs, settings. Inside core it's plain frozen dataclasses. Feature sandboxes are exempt:
inside a sandbox, anything goes. This is pragmatic, since these sandboxes can easily be bigger than
the rest of the repo and take the full attention of a team.

* Purity is about frameworks and I/O, not dependency count. For instance, utils and
core lean on stdlib and pure third-party libraries like numpy — while anything
that touches the outside world is structurally `forbidden`.

### Enforcement over documentation

A rule a tool enforces doesn't need prose, review vigilance, or reliance on
anyone's memory. The strategy here: the import-linter contracts and
arch checkers strictly protect the design. Everything else is commentary.
The four import contracts (in `pyproject.toml`):

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
4. **protected** — the inverse of forbidden: `sqlite3` may be imported *only*
   by `services.adapters`. Rather than naming who can't touch the database,
   it names the one place that can, so "I/O gets wrapped in an adapter" and
   "adapters live in services" become a single rule. (Features exempt again.)

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
