# tests/

Test strategy mirrors the tiers (docs/design-rules.md, Part 2 "Testing"):

| Suite | Scope | Style |
|---|---|---|
| `unit/` | utils + domain | pure in/out, **zero mocking**; shared builders in `builders.py` |
| `model/` | the ML core | train on synthetic data, assert AUC > 0.7 held-out; artifact-missing error path |
| `integration/` | api + ui through services | TestClient over a real sqlite tmp file; only the scorer is stubbed (the one true external boundary) |
| `arch/` | the codebase itself | custom AST checkers — see [arch/README.md](arch/README.md) |

Run: `just test` (everything) · `just arch` (architecture checks only).
