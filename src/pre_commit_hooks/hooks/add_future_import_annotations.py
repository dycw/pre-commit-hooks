from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from libcst import parse_statement
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.throttle import throttle

from pre_commit_hooks.constants import (
    THROTTLE_DURATION,
    paths_argument,
    throttle_option,
)
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
@paths_argument
@throttle_option
def _main(*, paths: tuple[Path, ...], throttle: bool = True) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p, throttle=throttle) for p in paths))


def _run(path: PathLike, /, *, throttle: bool = True) -> bool:
    modifications: set[Path] = set()
    func = _run_throttled if throttle else _run_unthrottled
    func(path, modifications=modifications)
    return len(modifications) == 0


def _run_unthrottled(
    path: PathLike, /, *, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_python_file(path, modifications=modifications) as context:
        if len(context.input.body) == 0:
            body = [parse_statement("from __future__ import annotations")]
            context.output = context.input.with_changes(body=body)


_run_throttled = throttle(
    duration=THROTTLE_DURATION,
    path=path_throttle_cache("add-future-import-annotations"),
)(_run_unthrottled)


if __name__ == "__main__":
    _main()
