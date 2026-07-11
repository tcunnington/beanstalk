"""Checker: LCOM4 cohesion — a class's methods must form one connected graph.

Nodes are the class's instance methods (dunders, staticmethods and
classmethods excluded). Two methods are connected when they share a
``self.X`` attribute or one calls the other. LCOM4 is the number of
connected components: 1 is cohesive, >= 2 means the class is really
several classes (ARCH301). Classes that touch no instance state are skipped.

Adapted from the approach in the `cohesion` PyPI package, reimplemented as
a small union-find rather than taking a stale dependency.
"""

import ast
from pathlib import Path

from tests.arch.checkers.config import Lcom4Config, Violation

_SKIPPED_METHOD_DECORATORS = {"staticmethod", "classmethod"}


def check_file(path: Path, config: Lcom4Config) -> list[Violation]:
    tree = ast.parse(path.read_text())
    violations: list[Violation] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            components = lcom4(node)
            if components > config.max_components:
                violations.append(
                    Violation(
                        file=path,
                        line=node.lineno,
                        code="ARCH301",
                        message=(
                            f"class {node.name} has LCOM4 = {components}: its methods form "
                            f"{components} unrelated groups; consider splitting the class"
                        ),
                    )
                )
    return violations


def lcom4(cls: ast.ClassDef) -> int:
    """Connected components among instance methods; 0 when there is nothing to measure."""
    methods = _instance_methods(cls)
    if len(methods) < 2:
        return 0
    attributes_used = {method.name: _self_attribute_names(method) for method in methods}
    method_names = set(attributes_used)
    calls_made = {name: attributes_used[name] & method_names for name in attributes_used}
    if not any(attributes_used.values()):
        return 0  # no instance state at all: nothing to be cohesive about

    parent = {name: name for name in method_names}
    _union_methods_sharing_attributes(parent, attributes_used, method_names)
    for caller, callees in calls_made.items():
        for callee in callees:
            _union(parent, caller, callee)
    return len({_find(parent, name) for name in method_names})


def _instance_methods(cls: ast.ClassDef) -> list[ast.FunctionDef]:
    methods = []
    for node in cls.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name == "__init__" or (node.name.startswith("__") and node.name.endswith("__")):
            continue
        decorator_names = {d.id for d in node.decorator_list if isinstance(d, ast.Name)}
        if decorator_names & _SKIPPED_METHOD_DECORATORS:
            continue
        methods.append(node)
    return methods


def _self_attribute_names(method: ast.FunctionDef) -> set[str]:
    """Names reached as ``self.X`` — both plain attributes and method calls."""
    return {
        node.attr
        for node in ast.walk(method)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    }


def _union_methods_sharing_attributes(
    parent: dict[str, str],
    attributes_used: dict[str, set[str]],
    method_names: set[str],
) -> None:
    first_user_of: dict[str, str] = {}
    for method_name, attributes in attributes_used.items():
        for attribute in attributes - method_names:
            if attribute in first_user_of:
                _union(parent, first_user_of[attribute], method_name)
            else:
                first_user_of[attribute] = method_name


def _find(parent: dict[str, str], name: str) -> str:
    while parent[name] != name:
        parent[name] = parent[parent[name]]
        name = parent[name]
    return name


def _union(parent: dict[str, str], first: str, second: str) -> None:
    parent[_find(parent, first)] = _find(parent, second)
