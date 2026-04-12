"""Sanity tests for release metadata files (VERSION, LICENSE, pyproject.toml)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_VERSION = "1.0.0"


def test_version_file_pinned():
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    assert version == EXPECTED_VERSION, f"VERSION mismatch: {version}"


def test_pyproject_version_matches_version_file():
    body = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{EXPECTED_VERSION}"' in body
    assert 'name = "neuralbot-omega"' in body


def test_license_file_present_and_mit():
    license_path = REPO_ROOT / "LICENSE"
    assert license_path.exists(), "LICENSE must exist for 1.0.0 release"
    body = license_path.read_text(encoding="utf-8")
    assert "MIT License" in body
    assert "WITHOUT WARRANTY OF ANY KIND" in body


def test_changelog_has_release_entry():
    body = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"[{EXPECTED_VERSION}]" in body
    assert "Final Build & Release" in body


def test_release_gate_script_runs_matrix_check():
    body = (REPO_ROOT / "scripts" / "release_gate.sh").read_text(encoding="utf-8")
    assert "check_implementation_matrix.py" in body
    assert "check_deprecated_imports.py" in body


def test_dockerfile_ships_migrations_and_version():
    body = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "migrations/" in body
    assert "alembic.ini" in body
    assert "VERSION" in body
    assert "LICENSE" in body
    assert "USER appuser" in body  # non-root container
