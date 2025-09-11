from __future__ import annotations

from importlib.resources import files
from subprocess import SubprocessError, run
from typing import TYPE_CHECKING, cast

from click import command

from pre_commit_hooks.common import run_all, run_every_option, throttled_run, write_text

if TYPE_CHECKING:
    from pathlib import Path

    from whenever import DateTimeDelta


@command()
@run_every_option
def main(*, run_every: DateTimeDelta | None = None) -> bool:
    """CLI for the `check-submodules-updated` hook."""
    return throttled_run("check-submodules-updated", run_every, _process)


def _process() -> bool:
    file = cast("Path", files("pre_commit_hooks")).joinpath(
        "check_submodules_updated", "check-submodules-updated"
    )
    try:
        _ = run([str(file)], check=True)
    except SubprocessError:
        return False
    return True


__all__ = ["main", "run_all", "write_text"]
