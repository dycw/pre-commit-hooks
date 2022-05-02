#!/usr/bin/env python3
from logging import basicConfig
from logging import info
from re import search
from subprocess import check_output  # noqa: S404
from sys import stdout
from typing import List


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    return int(not _process())


def _process() -> bool:
    deps = _scan_deps()
    if len(deps) >= 1:
        info(deps)
        return False
    else:
        return True


def _scan_deps() -> List[str]:
    lines = check_output(  # noqa: S603, S607
        ["scan-deps", "poetry.lock", "pyproject.toml"], text=True
    ).rstrip("\n")
    return [line for line in lines if search(r"^direct\s+", lines)]


if __name__ == "__main__":
    raise SystemExit(main())
