from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command, option
from utilities.os import is_pytest

from pre_commit_hooks.constants import DYCW_PRE_COMMIT_HOOKS_URL, RUFF_URL
from pre_commit_hooks.utilities import add_pre_commit_config_repo, run_all_maybe_raise

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p) for p in paths))


def _run(path: PathLike, /) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        RUFF_URL,
        "ruff-check",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", ["--fix"]),
        type_="linter",
    )
    add_pre_commit_config_repo(
        RUFF_URL,
        "ruff-format",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
