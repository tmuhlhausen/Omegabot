from pathlib import Path
import importlib.util


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_implementation_matrix.py"
spec = importlib.util.spec_from_file_location("check_implementation_matrix", SCRIPT_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_validate_matrix_fails_for_release_critical_scaffold(tmp_path):
    matrix = tmp_path / "IMPLEMENTATION_MATRIX.md"
    matrix.write_text(
        """
| ID | Capability | Code path | Status | Test coverage | Operational metric | Owner | Release critical |
|---|---|---|---|---|---|---|---|
| IM-X | Demo | src/x.py | scaffold | untested | metric | team | yes |
""".strip(),
        encoding="utf-8",
    )

    ok, failures = module.validate_matrix(matrix)

    assert ok is False
    assert failures
    assert "IM-X" in failures[0]


def test_validate_matrix_passes_for_release_critical_tested(tmp_path):
    matrix = tmp_path / "IMPLEMENTATION_MATRIX.md"
    matrix.write_text(
        """
| ID | Capability | Code path | Status | Test coverage | Operational metric | Owner | Release critical |
|---|---|---|---|---|---|---|---|
| IM-Y | Demo | src/y.py | partial | unit | metric | team | yes |
| IM-Z | Demo2 | src/z.py | scaffold | untested | metric | team | no |
""".strip(),
        encoding="utf-8",
    )

    ok, failures = module.validate_matrix(matrix)

    assert ok is True
    assert failures == []
