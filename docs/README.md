# docs/

Project-level design documentation — the "why" behind the code.

- [design-rules.md](design-rules.md) — **The Layered Pragmatist**: the house software
  design & clean code guide. The authoritative text; tooling and code conform to it.
- [enforcement-map.md](enforcement-map.md) — each rule in the guide mapped to the
  tool/contract/checker that enforces it (or marked review-only).
- [adopting-this.md](adopting-this.md) — porting this setup to a *different*
  app: how to map your own domain onto the tiers, not just copy this one's.

Nothing in here is code. Architecture-as-code lives in `pyproject.toml`
(import-linter contracts, archcheck config) and `tests/arch/`.
