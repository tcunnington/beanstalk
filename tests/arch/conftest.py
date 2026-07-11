"""Shared plumbing for the architecture checks."""

from pathlib import Path

from tests.arch.checkers.config import ArchcheckConfig, load_config, source_files

FIXTURES_DIR = Path(__file__).parent / "fixtures"

CONFIG: ArchcheckConfig = load_config()
SOURCE_FILES = source_files(CONFIG)


def source_file_id(path: Path) -> str:
    return str(path.relative_to(CONFIG.source_root))
