#!/usr/bin/env python3
from logging import basicConfig
from logging import error
from logging import info
from re import search
from subprocess import check_output  # noqa: S404
from sys import stdout
from typing import List
from typing import Optional


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    return int(not _process())


def _process() -> bool:
    deps = _scan_deps()
    if deps is None:
        return False
    else:
        if len(deps) >= 1:
            info(deps)
            return False
        else:
            return True


def _scan_deps() -> Optional[List[str]]:
    cmd = ["scan-deps", "poetry.lock", "pyproject.toml"]
    try:
        lines = check_output(cmd, text=True).rstrip("\n")  # noqa: S603
    except FileNotFoundError:
        error(
            "Failed to run %r. Is `poetry-deps-scanner` installed?",
            " ".join(cmd),
        )
        return None
    else:
        return [line for line in lines if search(r"^direct\s+", lines)]


if __name__ == "__main__":
    raise SystemExit(main())