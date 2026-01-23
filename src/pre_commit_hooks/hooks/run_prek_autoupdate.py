from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, read_text
from utilities.subprocess import run
from utilities.throttle import throttle

from pre_commit_hooks.constants import (
    PRE_COMMIT_CONFIG_YAML,
    THROTTLE_DURATION,
    paths_argument,
    throttle_option,
)
from pre_commit_hooks.utilities import (
    add_modification,
    path_throttle_cache,
    run_all_maybe_raise,
)

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path


@command(**CONTEXT_SETTINGS)
@paths_argument
@throttle_option
def _main(*, paths: tuple[Path, ...], throttle: bool = True) -> None:
    if is_pytest():
        return
    if len(paths) >= 1:
        run_all_maybe_raise(partial(_run, throttle=throttle))


def _run(*, throttle: bool = False) -> bool:
    modifications: set[Path] = set()
    func = _run_throttled if throttle else _run_unthrottled
    func(modifications=modifications)
    return len(modifications) == 0


def _run_unthrottled(*, modifications: MutableSet[Path] | None = None) -> None:
    init = read_text(PRE_COMMIT_CONFIG_YAML)
    run("prek", "autoupdate")
    if read_text(PRE_COMMIT_CONFIG_YAML) != init:
        add_modification(PRE_COMMIT_CONFIG_YAML, modifications=modifications)


_run_throttled = throttle(
    duration=THROTTLE_DURATION, path=path_throttle_cache("run-prek-autoupdate")
)(_run_unthrottled)


if __name__ == "__main__":
    _main()
