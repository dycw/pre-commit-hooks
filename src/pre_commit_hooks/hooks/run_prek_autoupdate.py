from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.subprocess import run

from pre_commit_hooks.constants import (
    PRE_COMMIT_CONFIG_YAML,
    paths_argument,
    throttle_option,
)
from pre_commit_hooks.utilities import run_all_maybe_raise

if TYPE_CHECKING:
    from pathlib import Path


@command(**CONTEXT_SETTINGS)
@paths_argument
@throttle_option
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    if len(paths) >= 1:
        run_all_maybe_raise(_run)


def _run() -> bool:
    current = PRE_COMMIT_CONFIG_YAML.read_text()
    run("prek", "autoupdate")
    return PRE_COMMIT_CONFIG_YAML.read_text() != current


if __name__ == "__main__":
    _main()
