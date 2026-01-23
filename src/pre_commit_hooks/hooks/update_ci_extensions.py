from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, move

from pre_commit_hooks.constants import paths_argument
from pre_commit_hooks.utilities import run_all_maybe_raise

if TYPE_CHECKING:
    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p) for p in paths))


def _run(path: PathLike, /) -> bool:
    new = Path(path).with_suffix(".yaml")
    move(path, new)
    return False


if __name__ == "__main__":
    _main()
