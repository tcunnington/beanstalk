"""Resolve local names in a module back to their dotted import origins.

Only static, direct references resolve (``from x import y``, ``import x`` +
``x.y``). Names bound by assignment (``logger = logging.getLogger(...)``)
intentionally do not — the checkers accept that blind spot for simplicity.
"""

import ast


def import_origins(tree: ast.Module) -> dict[str, str]:
    """Map names bound by imports to their dotted origin.

    ``from pydantic import BaseModel as BM`` -> ``{"BM": "pydantic.BaseModel"}``;
    ``import numpy as np`` -> ``{"np": "numpy"}``.
    """
    origins: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    origins[alias.asname] = alias.name
                else:
                    # `import a.b` binds only the top-level name `a`.
                    top_level = alias.name.split(".")[0]
                    origins[top_level] = top_level
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            for alias in node.names:
                origins[alias.asname or alias.name] = f"{node.module}.{alias.name}"
    return origins


def resolve_name(node: ast.expr, origins: dict[str, str]) -> str | None:
    """Resolve an expression like ``BM`` or ``typing.Protocol[T]`` to a dotted path."""
    parts = _attribute_parts(node)
    if not parts:
        return None
    head, *rest = parts
    return ".".join([origins.get(head, head), *rest])


def _attribute_parts(node: ast.expr) -> list[str] | None:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        value_parts = _attribute_parts(node.value)
        return [*value_parts, node.attr] if value_parts else None
    if isinstance(node, ast.Subscript):  # Protocol[T] -> Protocol
        return _attribute_parts(node.value)
    return None
