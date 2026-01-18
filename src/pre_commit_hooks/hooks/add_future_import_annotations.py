from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from libcst import parse_statement
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.throttle import throttle

from pre_commit_hooks.constants import THROTTLE_DURATION
from pre_commit_hooks.utilities import (
    path_throttle_cache,
    run_all_maybe_raise,
    yield_python_file,
)

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p) for p in paths))


def _run(path: PathLike, /) -> bool:
    modifications: set[Path] = set()
    _run_core(path, modifications=modifications)
    return len(modifications) == 0


def _run_core_unthrottled(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_python_file(path, modifications=modifications) as context:
        if len(context.input.body) == 1:
            body = [
                *context.input.body,
                parse_statement("from __future__ import annotations"),
            ]
            context.output = context.input.with_changes(body=body)


_run_core = throttle(
    duration=THROTTLE_DURATION,
    path=path_throttle_cache("add-future-import-annotations"),
)(_run_core_unthrottled)


if __name__ == "__main__":
    _main()
