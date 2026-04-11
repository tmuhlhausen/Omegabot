#!/usr/bin/env python3
"""Validate release-critical rows in docs/IMPLEMENTATION_MATRIX.md."""

from __future__ import annotations

from pathlib import Path

MATRIX_PATH = Path("docs/IMPLEMENTATION_MATRIX.md")
REQUIRED_COLUMNS = {
    "id",
    "status",
    "test coverage",
    "release critical",
}


def _normalize(value: str) -> str:
    return value.strip().lower()


def _parse_table(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists():
        raise RuntimeError(f"matrix not found: {path}")

    lines = [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()]
    table_lines = [line for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 3:
        raise RuntimeError("matrix table is missing or incomplete")

    header = [cell.strip() for cell in table_lines[0].strip().strip("|").split("|")]
    columns = [_normalize(cell) for cell in header]
    if not REQUIRED_COLUMNS.issubset(columns):
        missing = REQUIRED_COLUMNS.difference(columns)
        raise RuntimeError(f"matrix columns missing: {', '.join(sorted(missing))}")

    rows: list[dict[str, str]] = []
    for raw in table_lines[2:]:
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) != len(header):
            continue
        rows.append(dict(zip(columns, cells)))

    if not rows:
        raise RuntimeError("matrix has no data rows")

    return columns, rows


def validate_matrix(path: Path = MATRIX_PATH) -> tuple[bool, list[str]]:
    _, rows = _parse_table(path)
    failures: list[str] = []

    for row in rows:
        critical = _normalize(row["release critical"]) in {"yes", "true", "1"}
        if not critical:
            continue

        status = _normalize(row["status"])
        coverage = _normalize(row["test coverage"])

        if status == "scaffold" or coverage == "untested":
            failures.append(
                f"{row['id']}: status={row['status']}, test_coverage={row['test coverage']}"
            )

    return len(failures) == 0, failures


def main() -> int:
    try:
        ok, failures = validate_matrix()
    except RuntimeError as exc:
        print(f"❌ implementation matrix validation error: {exc}")
        return 1

    if not ok:
        print("❌ release-critical implementation rows are not release-ready:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("✅ implementation matrix release-critical checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
