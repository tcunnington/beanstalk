"""Typed access to the [tool.archcheck] configuration in pyproject.toml."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"

# The design-rule each code enforces, cited in every violation so the reader
# (human or agent) lands on the rationale, not just the symptom.
RULE_DOCS = {
    "ARCH101": "docs/design-rules.md 'Composition Over DI Frameworks'",
    "ARCH102": "docs/design-rules.md 'Composition Over DI Frameworks'",
    "ARCH201": "docs/design-rules.md 'Anemic Domain Models'",
    "ARCH202": "docs/design-rules.md 'Anemic Domain Models'",
    "ARCH301": "docs/design-rules.md 'Prefer Functions Over Classes'",
}


@dataclass(frozen=True)
class Violation:
    file: Path
    line: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.file}:{self.line} {self.code} {self.message} [{RULE_DOCS[self.code]}]"


@dataclass(frozen=True)
class NoInheritanceConfig:
    allowed_bases: frozenset[str]
    allow_exception_suffix: bool


@dataclass(frozen=True)
class ModelLogicConfig:
    max_cognitive_complexity: int
    io_import_prefixes: tuple[str, ...]


@dataclass(frozen=True)
class Lcom4Config:
    max_components: int


@dataclass(frozen=True)
class ArchcheckConfig:
    source_root: Path
    no_inheritance: NoInheritanceConfig
    model_logic: ModelLogicConfig
    lcom4: Lcom4Config


def load_config(pyproject_path: Path = PYPROJECT_PATH) -> ArchcheckConfig:
    with pyproject_path.open("rb") as pyproject_file:
        raw = tomllib.load(pyproject_file)["tool"]["archcheck"]
    return ArchcheckConfig(
        source_root=pyproject_path.parent / raw["source_root"],
        no_inheritance=NoInheritanceConfig(
            allowed_bases=frozenset(raw["no_inheritance"]["allowed_bases"]),
            allow_exception_suffix=raw["no_inheritance"].get("allow_exception_suffix", True),
        ),
        model_logic=ModelLogicConfig(
            max_cognitive_complexity=raw["model_logic"]["max_cognitive_complexity"],
            io_import_prefixes=tuple(raw["model_logic"]["io_import_prefixes"]),
        ),
        lcom4=Lcom4Config(max_components=raw["lcom4"]["max_components"]),
    )


def source_files(config: ArchcheckConfig) -> list[Path]:
    """Every Python file the checkers scan."""
    return sorted(config.source_root.rglob("*.py"))
