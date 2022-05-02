#!/usr/bin/env python3
from logging import basicConfig
from logging import error
from logging import info
from re import search
from subprocess import CalledProcessError  # noqa: S404
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
    cmd = ["scan-deps", "poetry.lock", "pyproject.toml"]
    try:
        lines = check_output(cmd, text=True).rstrip("\n")  # noqa: S603
    except CalledProcessError as cperror:
        if cperror.returncode != 1:
            error("Failed to run %r", " ".join(cmd))
        raise
    except FileNotFoundError:
        error("Failed to run %r. Is `bump2version` installed?", " ".join(cmd))
        raise
    except Exception:
        raise
    else:
        return [line for line in lines if search(r"^direct\s+", lines)]


if __name__ == "__main__":
    raise SystemExit(main())
