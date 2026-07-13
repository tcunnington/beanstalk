# tests/

Test strategy mirrors the tiers (docs/design-rules.md, Part 2 "Testing"):

| Suite | Scope | Style |
|---|---|---|
| `unit/` | utils + core | pure in/out, **zero mocking**; shared builders in `builders.py` |
| `features/` | each feature in isolation | risk_scorer: AUC > 0.7 on held-out synthetic data + artifact-missing path; machine_recommender through its entrypoint |
| `integration/` | api + ui + coordination through services | TestClient over a real sqlite tmp file; only the scorer is stubbed (the one true external boundary) |
| `arch/` | the codebase itself | custom AST checkers — see [arch/README.md](arch/README.md) |

Run: `just test` (everything) · `just arch` (architecture checks only).
