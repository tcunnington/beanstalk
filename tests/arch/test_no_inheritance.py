from pathlib import Path

import pytest

from tests.arch.checkers.no_inheritance import check_file
from tests.arch.conftest import CONFIG, FIXTURES_DIR, SOURCE_FILES, source_file_id


@pytest.mark.parametrize("path", SOURCE_FILES, ids=source_file_id)
def test_source_file_obeys_the_inheritance_allow_list(path: Path):
    violations = check_file(path, CONFIG.no_inheritance)
    assert not violations, "\n" + "\n".join(str(v) for v in violations)


def test_checker_flags_disallowed_and_multiple_bases():
    violations = check_file(FIXTURES_DIR / "bad_inheritance.py", CONFIG.no_inheritance)
    codes = [violation.code for violation in violations]
    assert codes.count("ARCH101") == 3  # Cow(Animal) + MultiCow(Animal, Mixin)
    assert codes.count("ARCH102") == 1  # MultiCow's multiple inheritance


def test_checker_accepts_every_allow_listed_base():
    assert check_file(FIXTURES_DIR / "good_inheritance.py", CONFIG.no_inheritance) == []
