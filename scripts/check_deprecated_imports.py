"""Static check: block imports from deprecated shim modules."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_ROOTS = ("src", "tests")
DEPRECATED_PREFIXES = ("strategies", "strategies.")


def _is_deprecated_module(name: str | None) -> bool:
    if not name:
        return False
    return name.startswith(DEPRECATED_PREFIXES)


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in CHECK_ROOTS:
        files.extend((REPO_ROOT / root).rglob("*.py"))
    return files


def _check_file(path: Path) -> list[str]:
    rel = path.relative_to(REPO_ROOT)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(rel))
    violations: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_deprecated_module(alias.name):
                    violations.append(
                        f"{rel}:{node.lineno} import {alias.name} is deprecated "
                        "(use src.strategies/import_map)."
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and _is_deprecated_module(node.module):
                violations.append(
                    f"{rel}:{node.lineno} from {node.module} import ... is deprecated "
                    "(use src.strategies/import_map)."
                )
    return violations


def main() -> int:
    failures: list[str] = []
    for pyfile in _iter_python_files():
        failures.extend(_check_file(pyfile))

    if failures:
        print("Deprecated import usage found:")
        for item in failures:
            print(f" - {item}")
        return 1
    print("No deprecated shim imports found in src/ and tests/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
