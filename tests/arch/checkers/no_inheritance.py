"""Checker: classes may only inherit from an allow-listed set of bases.

ARCH101 — a base class is not on the allow-list.
ARCH102 — multiple inheritance (structural bases Protocol/Generic exempt).

Bases are resolved through the file's imports, so ``from pydantic import
BaseModel`` matches the allow-list entry ``pydantic.BaseModel``. A locally
defined base keeps its bare name and only passes via the Error/Exception
suffix rule (when enabled).
"""

import ast
from pathlib import Path

from tests.arch.checkers.config import NoInheritanceConfig, Violation
from tests.arch.checkers.imports import import_origins, resolve_name

_STRUCTURAL_BASES = frozenset({"typing.Protocol", "typing.Generic"})


def check_file(path: Path, config: NoInheritanceConfig) -> list[Violation]:
    tree = ast.parse(path.read_text())
    origins = import_origins(tree)
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            violations.extend(_check_class(node, origins, config, path))
    return violations


def _check_class(
    cls: ast.ClassDef,
    origins: dict[str, str],
    config: NoInheritanceConfig,
    path: Path,
) -> list[Violation]:
    resolved_bases = [resolve_name(base, origins) or ast.unparse(base) for base in cls.bases]
    violations = [
        Violation(
            file=path,
            line=cls.lineno,
            code="ARCH101",
            message=(
                f"class {cls.name} inherits from {base!r}, which is not on the "
                "allow-list; compose it in, or define a Protocol"
            ),
        )
        for base in resolved_bases
        if not _is_allowed(base, config)
    ]
    substantive_bases = [base for base in resolved_bases if base not in _STRUCTURAL_BASES]
    if len(substantive_bases) > 1:
        violations.append(
            Violation(
                file=path,
                line=cls.lineno,
                code="ARCH102",
                message=(
                    f"class {cls.name} uses multiple inheritance "
                    f"({', '.join(resolved_bases)}); keep one base and compose the rest"
                ),
            )
        )
    return violations


def _is_allowed(base: str, config: NoInheritanceConfig) -> bool:
    if base in config.allowed_bases:
        return True
    simple_name = base.rsplit(".", 1)[-1]
    return config.allow_exception_suffix and simple_name.endswith(("Error", "Exception"))
