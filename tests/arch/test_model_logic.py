from pathlib import Path

import pytest

from tests.arch.checkers.model_logic import check_file
from tests.arch.conftest import CONFIG, FIXTURES_DIR, SOURCE_FILES, source_file_id


@pytest.mark.parametrize("path", SOURCE_FILES, ids=source_file_id)
def test_data_models_in_source_stay_bare(path: Path):
    violations = check_file(path, CONFIG.model_logic)
    assert not violations, "\n" + "\n".join(str(v) for v in violations)


def test_checker_flags_complex_logic_and_io_in_data_models():
    violations = check_file(FIXTURES_DIR / "bad_data_models.py", CONFIG.model_logic)
    codes = {violation.code for violation in violations}
    assert codes == {"ARCH201", "ARCH202"}


def test_checker_accepts_derived_properties_formatting_and_validators():
    assert check_file(FIXTURES_DIR / "good_data_models.py", CONFIG.model_logic) == []
