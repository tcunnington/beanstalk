from pathlib import Path

import pytest

from tests.arch.checkers.lcom4 import check_file
from tests.arch.conftest import CONFIG, FIXTURES_DIR, SOURCE_FILES, source_file_id


@pytest.mark.parametrize("path", SOURCE_FILES, ids=source_file_id)
def test_source_classes_are_cohesive(path: Path):
    violations = check_file(path, CONFIG.lcom4)
    assert not violations, "\n" + "\n".join(str(v) for v in violations)


def test_checker_flags_a_class_with_two_unrelated_method_groups():
    violations = check_file(FIXTURES_DIR / "bad_cohesion.py", CONFIG.lcom4)
    assert [violation.code for violation in violations] == ["ARCH301"]
    assert "LCOM4 = 2" in violations[0].message


def test_checker_accepts_cohesive_and_stateless_classes():
    assert check_file(FIXTURES_DIR / "good_cohesion.py", CONFIG.lcom4) == []
