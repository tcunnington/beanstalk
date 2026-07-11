# tests/arch/ — custom architecture checks

Three AST-based checkers, run as pytest (one test per source file → readable
failures). Config lives in `pyproject.toml` under `[tool.archcheck]`.

| Code | Checker | Rule |
|---|---|---|
| ARCH101 | `checkers/no_inheritance.py` | every base class must be on the allow-list (Exception, Protocol, BaseModel, Enum, … — deliberately **not** `abc.ABC`); Error/Exception-suffixed bases allowed |
| ARCH102 | 〃 | no multiple inheritance (structural Protocol/Generic bases exempt) |
| ARCH201 | `checkers/model_logic.py` | data models (@dataclass, BaseModel, attrs, NamedTuple, TypedDict) keep every method under a cognitive-complexity threshold ([complexipy](https://github.com/rohaquinlop/complexipy)); pydantic validators exempt |
| ARCH202 | 〃 | data-model methods never call deny-listed I/O prefixes (logging, sqlite3, services, …) — auto-fail regardless of complexity |
| ARCH301 | `checkers/lcom4.py` | LCOM4 = 1: a class's methods form one connected component (edges: shared `self.X` or method-calls-method; union-find; adapted from the `cohesion` package's approach, not a dependency) |

`checkers/imports.py` resolves local names to dotted import origins (shared by
101/201). `checkers/config.py` loads `[tool.archcheck]` via stdlib `tomllib`.

## fixtures/

Known-bad and known-good snippets, **parsed but never imported**. Each checker's
test asserts it flags the bad fixture and passes the good one — so "the linter
would catch that" stays a *verified* claim, permanently.

## Known blind spots (accepted for simplicity)

- names bound by assignment don't resolve (`logger = logging.getLogger()` hides
  the `logging` prefix from ARCH202)
- data-model detection is per-file: a class inheriting a BaseModel *subclass*
  isn't detected — but ARCH101 forbids that inheritance anyway
- LCOM4 skips staticmethods/classmethods and top-level-nested classes only
