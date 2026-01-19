from __future__ import annotations

from functools import partial
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest

from pre_commit_hooks.constants import BUMPVERSION_TOML, paths_argument
from pre_commit_hooks.utilities import (
    get_version_from_path,
    run_all_maybe_raise,
    set_version,
)

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))


def _run(*, path: PathLike = BUMPVERSION_TOML) -> bool:
    version = get_version_from_path(path=path)
    try:
        set_version(version, path=path)
    except CalledProcessError:
        return False
    return True


if __name__ == "__main__":
    _main()
