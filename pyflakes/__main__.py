"""Entry point for the offline pyflakes stub."""
from __future__ import annotations

import argparse
import pathlib
import py_compile
import sys
from typing import Iterable


def iter_python_files(paths: Iterable[str]) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for raw in paths:
        path = pathlib.Path(raw)
        if path.is_dir():
            for candidate in path.rglob("*.py"):
                files.append(candidate)
        elif path.suffix == ".py" and path.exists():
            files.append(path)
        else:
            print(f"warning: skipping non-python path {path}", file=sys.stderr)
    return files


def check_file(path: pathlib.Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except py_compile.PyCompileError as exc:  # pragma: no cover - informative branch
        print(exc.msg, file=sys.stderr)
        return False


def check_paths(paths: Iterable[str]) -> int:
    files = iter_python_files(paths)
    if not files:
        print("no python files found", file=sys.stderr)
        return 1
    success = True
    for file_path in files:
        success &= check_file(file_path)
    return 0 if success else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline pyflakes syntax stub")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args(argv)
    return check_paths(args.paths)


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main())
