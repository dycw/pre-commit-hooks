from __future__ import annotations

from functools import partial
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from utilities.os import is_pytest
from utilities.subprocess import run

from pre_commit_hooks.constants import BUMPVERSION_TOML
from pre_commit_hooks.utilities import get_version_from_path, run_all_maybe_raise

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))


def _run(*, path: PathLike = BUMPVERSION_TOML) -> bool:
    version = get_version_from_path(path=path)
    try:
        run("bump-my-version", "replace", "--new-version", str(version), str(path))
    except CalledProcessError:
        return False
    return True


if __name__ == "__main__":
    _main()
