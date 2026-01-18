from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command, option
from utilities.os import is_pytest

from pre_commit_hooks.constants import URL
from pre_commit_hooks.utilities import add_pre_commit_config_repo, run_all_maybe_raise

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
@option("--ruff", is_flag=False, default=True)
def _main(*, paths: tuple[Path, ...], ruff: bool) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = []
    if ruff:
        funcs.extend(partial(_add_ruff_hooks, p) for p in paths)
    run_all_maybe_raise(*funcs)


def _add_ruff_hooks(path: PathLike, /) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        URL,
        "add-ruff-hooks",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
