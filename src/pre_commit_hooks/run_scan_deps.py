#!/usr/bin/env python3
from logging import basicConfig
from logging import error
from logging import info
from re import search
from subprocess import check_output  # noqa: S404
from sys import stdout


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    return int(not _process())


def _process() -> bool:
    deps = _scan_deps()
    if deps is None:
        return False
    else:
        if len(deps) >= 1:
            for dep in deps:
                info(dep)
            return False
        else:
            return True


def _scan_deps() -> list[str] | None:
    cmd = ["scan-deps", "poetry.lock", "pyproject.toml"]
    try:
        text = check_output(cmd, text=True).rstrip("\n")  # noqa: S603
    except FileNotFoundError:
        error(
            "Failed to run %r. Is `poetry-deps-scanner` installed?",
            " ".join(cmd),
        )
        return None
    else:
        return [
            line for line in text.splitlines() if search(r"^direct\s+", line)
        ]


if __name__ == "__main__":
    raise SystemExit(main())
