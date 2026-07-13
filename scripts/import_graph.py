"""Render the repo's import graph as a self-contained interactive HTML page.

Reads the same graph import-linter checks (via grimp) and the layer order
straight from the layers contract in pyproject.toml, so the picture always
matches what the import contracts actually enforce. Run with `just graph`.
"""

import json
import sys
import tomllib
from pathlib import Path

import grimp

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = Path(__file__).with_name("import_graph_template.html")
OUTPUT_PATH = REPO_ROOT / "import-graph.html"


def main() -> None:
    config = _importlinter_config()
    root = config["root_package"]
    layers = [[pkg.strip() for pkg in layer.split("|")] for layer in _layers_contract(config)]
    graph = grimp.build_graph(root, include_external_packages=True)

    packages = [pkg for layer in layers for pkg in layer]
    modules = sorted(
        m for m in graph.modules if m.startswith(root) and _package_of(m, packages) is not None
    )
    payload = {
        "root": root,
        "layers": layers,
        "groups": {
            pkg: [m for m in modules if _package_of(m, packages) == pkg] for pkg in packages
        },
        "edges": _internal_edges(graph, modules, packages, _seam_patterns(config)),
        "externals": _external_imports(graph, modules, root),
        "flagged": _flagged_externals(config),
    }
    html = TEMPLATE_PATH.read_text().replace("/*__DATA__*/", json.dumps(payload))
    OUTPUT_PATH.write_text(html)
    print(f"wrote {OUTPUT_PATH.relative_to(REPO_ROOT)} — open it in a browser or preview panel")


def _importlinter_config() -> dict:
    with (REPO_ROOT / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)["tool"]["importlinter"]


def _layers_contract(config: dict) -> list[str]:
    for contract in config["contracts"]:
        if contract["type"] == "layers":
            return contract["layers"]
    sys.exit("no layers contract found in [tool.importlinter]")


def _package_of(module: str, packages: list[str]) -> str | None:
    """The contract package a module belongs to (longest prefix wins)."""
    candidates = [p for p in packages if module == p or module.startswith(p + ".")]
    return max(candidates, key=len) if candidates else None


def _internal_edges(
    graph: grimp.ImportGraph,
    modules: list[str],
    packages: list[str],
    seams: list[tuple[str, str]],
) -> list[list]:
    edges = []
    for importer in modules:
        for imported in sorted(graph.find_modules_directly_imported_by(importer)):
            if imported not in modules:
                continue
            seam = any(
                importer.startswith(a) and imported.startswith(b) for a, b in seams
            ) and _package_of(importer, packages) != _package_of(imported, packages)
            edges.append([importer, imported, seam])
    return edges


def _seam_patterns(config: dict) -> list[tuple[str, str]]:
    """ignore_imports patterns as (importer_prefix, imported_prefix) pairs."""
    patterns = []
    for contract in config["contracts"]:
        for rule in contract.get("ignore_imports", []):
            importer, _, imported = rule.partition("->")
            patterns.append(
                (importer.strip().removesuffix(".**"), imported.strip().removesuffix(".**"))
            )
    return patterns


def _external_imports(
    graph: grimp.ImportGraph, modules: list[str], root: str
) -> dict[str, list[str]]:
    """Non-stdlib imports per module (plus stdlib I/O modules worth flagging)."""
    externals: dict[str, list[str]] = {}
    for module in modules:
        libs = sorted(
            imported
            for imported in graph.find_modules_directly_imported_by(module)
            if not imported.startswith(root)  # externals are squashed to top-level names
        )
        interesting = [
            lib for lib in libs if lib not in sys.stdlib_module_names or lib == "sqlite3"
        ]
        if interesting:
            externals[module] = interesting
    return externals


def _flagged_externals(config: dict) -> list[str]:
    """The forbidden-contract deny-list: frameworks and I/O, shown in red."""
    for contract in config["contracts"]:
        if contract["type"] == "forbidden":
            return contract["forbidden_modules"]
    return []


if __name__ == "__main__":
    main()
