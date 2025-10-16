from __future__ import annotations

from importlib.resources import files
from stat import S_IXUSR
from subprocess import SubprocessError, run
from typing import TYPE_CHECKING, cast

from click import command

from pre_commit_hooks.common import run_all, run_every_option, throttled_run, write_text

if TYPE_CHECKING:
    from pathlib import Path


@command()
def main() -> bool:
    """CLI for the `check-version-bumped` hook."""
    return _process()


def _process() -> bool:
    file = cast("Path", files("pre_commit_hooks")).joinpath(
        "check_version_bumped", "check-version-bumped"
    )
    file.chmod(file.stat().st_mode | S_IXUSR)
    try:
        _ = run([str(file)], check=True)
    except SubprocessError:
        return False
    return True


__all__ = ["main", "run_all", "run_every_option", "throttled_run", "write_text"]
