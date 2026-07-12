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
- **`domain` (tier 2)** is the business itself — frozen dataclasses plus pure
  functions: eligibility rules, affordability caps, and `decide()`, which
  combines them with a risk score. No I/O, no frameworks. Changes only when
  the business does.
- **`services` (tier 3)** is orchestration: load the model, score, decide,
  persist. It changes constantly — which is exactly why nothing below it may
  know it exists. Churn cannot propagate downward.

Crossed with the tiers are the **vertical apps**: `api`, `ui`, and `model`,
mutually independent. The API doesn't know the UI exists, and neither may
import the model directly. When the API needs a risk score it goes through
`services`, which hides the model behind a one-method `RiskScorer` Protocol.
That single seam is what makes the system testable: integration tests swap in
a `StubScorer` and never load sklearn.

Who wires it all together? `build_application_service()` in
[services/applications.py](src/beanstalk/services/applications.py) — the
composition root. Plain constructor calls (settings → repository + scorer →
service), no DI framework.

### The design principles the code actually follows

The house guide, [docs/design-rules.md](docs/design-rules.md) ("The Layered
Pragmatist"), is authoritative. The load-bearing rules as applied here:

- **Anemic data models.** Dataclasses carry data; logic lives in domain
  functions or services. `Decision.summary()` — one line of formatting — is
  about the ceiling of what a method on a data model may do.
- **Functions over classes.** The domain layer has zero behavior classes. The
  only classes with behavior hold *real state*: a sqlite connection
  (`DecisionRepository`), a loaded artifact (`RiskModel`).
- **Protocols, not ABCs.** `RiskScorer` is a `typing.Protocol`; implementers
  don't inherit anything. `abc.ABC` is deliberately banned from the
  inheritance allow-list.
- **Declines are values.** A declined application is a normal business
  outcome, so it's a return value (`Decision` with reasons) — never an
  exception. Exceptions mark the genuinely unexpected
  (`ApplicationNotFoundError` → 404), caught narrowly, chained with
  `raise ... from`.
- **Pydantic at boundaries only.** Validation happens where untrusted data
  enters: API schemas, UI forms, model features, settings. Inside, everything
  is plain frozen dataclasses — and the import contracts make that mechanical
  fact, not convention.

### The machine checks: enforce > document

A rule that a tool enforces needs no prose, no review vigilance, and no space
in anyone's memory. The three import-linter contracts (in `pyproject.toml`):

1. **layers** — the diagram above, literally: `(api | ui) → services → model
   → domain → utils`. Any upward import fails with the exact chain.
2. **independence** — api, ui, model may not import each other. Layering alone
   would still let the API `import beanstalk.model`; this contract forces the
   services seam. (Subtlety: independence counts *transitive* chains too, so
   the legitimate `services → model` edge is `ignore_imports`-ed, leaving
   exactly the rule we want — no *direct* imports.)
3. **forbidden** — utils and domain may not import pydantic, fastapi, sklearn,
   sqlite3… Tier purity, mechanically.

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
| The business, end to end | [domain/decisioning.py](src/beanstalk/domain/decisioning.py), then [services/applications.py](src/beanstalk/services/applications.py) |
