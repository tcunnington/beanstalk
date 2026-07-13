# Adopting this in a new repo

This repo is a **reference implementation**, not a template to photocopy.
"Make my repo look like Beanstalk" is the wrong instruction — it produces an
artificial `model/`-style package where your app has none, or five verticals
forced onto a domain that needs two. The right instruction is: *adopt the
spec* (`docs/design-rules.md`, machine-enforced via the contracts and
checkers), then *map your own domain* onto it. This document is that mapping
procedure — the missing piece the design-rules guide itself doesn't cover,
because it's necessarily domain-specific.

Written as a checklist an agent can execute directly. If you're kicking off a
new repo with an agent, point it at this file first.

## Step 0: What to vendor unchanged

Don't re-derive these — copy them. [enforcement-map.md](enforcement-map.md)'s
**Essential vs. swappable** table is the authoritative list; the short version:

- `docs/design-rules.md`, verbatim (edit only if your house rules genuinely differ)
- `tests/arch/checkers/` + `tests/arch/fixtures/` — the AST checkers and their
  known-bad proofs are domain-agnostic, config-driven via `[tool.archcheck]`
- the three import-contract *types* (layers, independence, forbidden) —
  the specific package names inside them are yours to fill in
- `scripts/import_graph.py` + `just graph` — reads the contracts, needs no edits
- the CLAUDE.md → docs/ funnel structure

What's genuinely this repo's taste (FastAPI, sqlite, sklearn, `just`) is called
out in the same table. Swap freely.

## Step 1: Sort your code into tiers

For each module you're about to write, ask in order — this is the actual
decision procedure, not just the tier definitions:

1. **Does it have an entry point or framework callback surface?** (HTTP route,
   CLI `main`, Airflow DAG, queue consumer, cron job) → it's an **interface**
   (`interfaces/`). Interfaces are dumb edges: parse input, call a service,
   format output. Nothing else.
2. **Does it touch the world** — network, disk, a message queue, the clock as
   a dependency, subprocess, env vars? → **tier 4, as a service or an
   adapter** (see Step 3). "Touching the world" means I/O, not "uses a
   library" — a heavyweight pure computation (see the aside below) still
   isn't this.
3. **Is it a decision, calculation, or transformation of business
   concepts, expressible without I/O?** → **tier 2 (core)** if the concept is
   shared by every capability in your app; **tier 3 (a feature)** if it's
   specific to one product capability. The operational test either way: can
   you unit-test it with literal values and zero mocks?
4. **None of the above, and zero business context** → **tier 1 (utils)**. The
   test: could this file be open-sourced without leaking anything about your
   business *or* your infrastructure? An S3 wrapper is generic-looking but
   knows boto3 exists and fails without a network — it flunks. Utils is about
   *knowledge*, not reusability.

**Aside — pure but heavyweight.** Code with no I/O but a large dependency
(pandas transforms, a numpy-heavy calculation) is genuinely ambiguous. There's
no universal answer; this repo's answer is "core speaks stdlib only, utils may
use pure third-party libraries" (see the `forbidden` contract's deny-list).
Decide your own per-repo vocabulary for what each pure tier may speak, and
encode it in the deny-list — that's what the contract is *for*.

## Step 2: Decide your verticals

Two independent kinds of "sideways" module exist, and conflating them is the
single most common mapping mistake:

- **Interfaces** (Step 1.1) are delivery mechanisms. Multiple interfaces can
  front the *same* capability (the API and the UI both submit financing
  applications here).
- **Feature sandboxes** (tier 3) are product capabilities — the things your
  app *does*, each big enough to need its own internal structure, its own
  dependencies, and its own team. Interfaces and features relate
  **many-to-many, always through services** — never directly.

**Worked example from this repo.** The original plan had a `model/` package —
"the ML core product" — sitting awkwardly between `services` and `domain`,
neither a delivery mechanism nor obviously core. Once a second capability
(equipment recommendations) was added, the ambiguity resolved itself: `model/`
was always a **feature** — a large, complex, product-specific capability that
must stay independent of any other capability added later. It became
`features/risk_scorer/`, parallel to `features/machine_recommender/`. If your
app has exactly one big capability, it can be tempting to special-case it
("tier 2.5", or merge it into core) — resist that. Structure for the second
capability from the start, even a stub one; that's cheaper than migrating
later and it's the fastest way to prove your `independence` contract catches
real violations.

**The metaphor that keeps this straight:** if this were microservices instead
of a modular monolith, each **feature** would be a service, and the
**services tier** would be the pub/sub bus wiring them together. Two features
that need to cooperate meet at the bus, never in a private back channel — the
`independence` contract makes that literal, not just aspirational.

## Step 3: Infrastructure — adapters and stores, not "repositories"

Tier-4 infrastructure code (Step 1.2) should itself split in two:

- **A generic adapter** — table/resource-shaped, zero business vocabulary,
  could be copied into an unrelated project verbatim. `services/adapters/sqlite.py`'s
  `SqliteAdapter` in this repo: `upsert(table, values)`, `find_one(table,
  column=, value=)` — it has never heard of a "decision".
- **A business-named store or client** on top, one per persisted concept, that
  owns the schema and the domain-object (de)serialization and calls the
  adapter for mechanics. `services/decision_records.py`'s `DecisionRecordStore`.

Avoid naming the top layer after a pattern instead of its content —
`Repository` says nothing about *what* is stored; `DecisionRecordStore` does.
Name infra classes the same way you'd name a core type: for the business
concept, not the mechanism. The same split applies to a queue adapter, a blob
store, an external API client — generic mechanics underneath, a
business-named wrapper on top, both living in `services/`, never in `utils/`.

## Step 4: Scaffold order

Wire the contracts **before** writing the first line of business code:

1. Create the empty packages for your tiers (Step 1) and verticals (Step 2).
2. Write the three import contracts against those empty packages — they pass
   trivially with zero code. This is the point: from the very first import
   onward, every line is written under enforcement, not retrofitted.
3. Vendor the AST checkers (Step 0); point `source_root` at your tree.
4. Only now start writing core types, then features, then services, then interfaces.

Retrofitting contracts onto an existing codebase is a different, harder
exercise — every pre-existing violation becomes a negotiation instead of a
build failure. If you're stuck doing that, start the `forbidden` and
`independence` contracts first (they tend to have fewer legacy violations
than `layers`), and consider `ignore_imports` as a temporary allow-list for
known debt, with a follow-up ticket to shrink it.

## Step 5: Calibrate the dials

Not everything you enforce has a correct value. See enforcement-map.md's
**Binary rules vs. dials** section for the full framing; in short — import
contracts and the inheritance allow-list are binary and can block a
greenfield build on day one. Complexity/cohesion/size ceilings are dials with
no correct value, only a current one: start them informational (the
justfile's `-` prefix pattern), and either tighten by hand or ratchet
(fail only on regression from a recorded baseline) once you have a real
distribution to calibrate against. A guessed threshold should never block a
merge on day one.

## Worksheet

Answer these before writing code, and keep the answers — they're the
domain-mapping decisions an agent (or a new teammate) can't derive from the
code alone:

- What are this app's core, enterprise-wide truths (tier 2)? What must every
  feature agree on?
- What are the product capabilities (tier 3)? Even with one today, what would
  a second look like — sketch its entrypoint signature now.
- What delivery mechanisms does this need (tier 4 interfaces)? Which
  capabilities does each one reach, and through which service methods?
- What infrastructure does coordination own (tier 4 adapters)? For each,
  what's the generic mechanic vs. the business-specific meaning?
- Which of your dial thresholds are borrowed from this repo and need
  re-tuning to your codebase's actual size and history?
