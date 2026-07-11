"""Checker: data-model classes must stay anemic (docs/design-rules.md Part 2).

ARCH201 — a method's cognitive complexity (via complexipy) exceeds the
          threshold; derived properties and formatting stay trivially simple.
ARCH202 — a method calls into a deny-listed import prefix (I/O, services);
          data models must never touch infrastructure, whatever their score.

Data models are detected by decorator (@dataclass, attrs) or base
(pydantic.BaseModel, BaseSettings, NamedTuple, TypedDict) on top-level
classes. Pydantic @field_validator/@model_validator methods are exempt —
boundary parsing is their job.
"""

import ast
from pathlib import Path

import complexipy

from tests.arch.checkers.config import ModelLogicConfig, Violation
from tests.arch.checkers.imports import import_origins, resolve_name

_DATA_MODEL_DECORATORS = frozenset(
    {"dataclasses.dataclass", "dataclass", "attr.s", "attrs.define", "attrs.frozen"}
)
_DATA_MODEL_BASES = frozenset(
    {
        "pydantic.BaseModel",
        "pydantic_settings.BaseSettings",
        "typing.NamedTuple",
        "typing.TypedDict",
    }
)
_EXEMPT_METHOD_DECORATORS = frozenset({"field_validator", "model_validator"})


def check_file(path: Path, config: ModelLogicConfig) -> list[Violation]:
    source = path.read_text()
    tree = ast.parse(source)
    origins = import_origins(tree)
    complexity_by_name = {
        entry.name: entry.complexity for entry in complexipy.code_complexity(source).functions
    }
    violations: list[Violation] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and _is_data_model(node, origins):
            violations.extend(_check_methods(node, origins, complexity_by_name, config, path))
    return violations


def _is_data_model(cls: ast.ClassDef, origins: dict[str, str]) -> bool:
    decorators = {resolve_name(_undecorate(d), origins) for d in cls.decorator_list}
    if decorators & _DATA_MODEL_DECORATORS:
        return True
    bases = {resolve_name(base, origins) for base in cls.bases}
    return bool(bases & _DATA_MODEL_BASES)


def _check_methods(
    cls: ast.ClassDef,
    origins: dict[str, str],
    complexity_by_name: dict[str, int],
    config: ModelLogicConfig,
    path: Path,
) -> list[Violation]:
    violations: list[Violation] = []
    for method in _checkable_methods(cls, origins):
        complexity = complexity_by_name.get(f"{cls.name}::{method.name}", 0)
        if complexity > config.max_cognitive_complexity:
            violations.append(
                Violation(
                    file=path,
                    line=method.lineno,
                    code="ARCH201",
                    message=(
                        f"data model {cls.name}.{method.name} has cognitive complexity "
                        f"{complexity} (max {config.max_cognitive_complexity}); "
                        "move the logic to the domain or service layer"
                    ),
                )
            )
        violations.extend(_io_call_violations(cls, method, origins, config, path))
    return violations


def _checkable_methods(cls: ast.ClassDef, origins: dict[str, str]) -> list[ast.FunctionDef]:
    methods = []
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef) or _is_dunder(node.name):
            continue
        decorators = {
            (resolve_name(_undecorate(d), origins) or "").rsplit(".", 1)[-1]
            for d in node.decorator_list
        }
        if decorators & _EXEMPT_METHOD_DECORATORS:
            continue
        methods.append(node)
    return methods


def _io_call_violations(
    cls: ast.ClassDef,
    method: ast.FunctionDef,
    origins: dict[str, str],
    config: ModelLogicConfig,
    path: Path,
) -> list[Violation]:
    violations = []
    for node in ast.walk(method):
        if not isinstance(node, ast.Call):
            continue
        called = resolve_name(node.func, origins)
        if called is None:
            continue
        prefix = _matching_prefix(called, config.io_import_prefixes)
        if prefix is not None:
            violations.append(
                Violation(
                    file=path,
                    line=node.lineno,
                    code="ARCH202",
                    message=(
                        f"data model {cls.name}.{method.name} calls {called!r} "
                        f"(deny-listed prefix {prefix!r}); data models must not touch I/O"
                    ),
                )
            )
    return violations


def _matching_prefix(called: str, prefixes: tuple[str, ...]) -> str | None:
    for prefix in prefixes:
        if called == prefix or called.startswith(prefix + "."):
            return prefix
    return None


def _undecorate(decorator: ast.expr) -> ast.expr:
    return decorator.func if isinstance(decorator, ast.Call) else decorator


def _is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__")
