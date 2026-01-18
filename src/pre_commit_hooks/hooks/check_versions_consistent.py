from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from utilities.os import is_pytest

from pre_commit_hooks.constants import BUMPVERSION_TOML, RUFF_TOML, RUFF_URL
from pre_commit_hooks.utilities import add_pre_commit_config_repo, run_all_maybe_raise

if TYPE_CHECKING:
    from utilities.types import PathLike


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))


def _run(*, path: PathLike = BUMPVERSION_TOML) -> bool:
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
    _add_ruff_toml(
        path=Path(path).parent / RUFF_TOML,
        modifications=modifications,
        python_version=python_version,
    )
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
