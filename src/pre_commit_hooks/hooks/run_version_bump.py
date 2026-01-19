from __future__ import annotations

from functools import partial
from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.version import Version3, Version3Error

from pre_commit_hooks.constants import BUMPVERSION_TOML, paths_argument
from pre_commit_hooks.utilities import (
    get_version_from_git_show,
    get_version_from_git_tag,
    get_version_from_path,
    run_all_maybe_raise,
    run_bump_my_version,
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
    try:
        prev = get_version_from_git_tag()
    except (CalledProcessError, ValueError):
        try:
            prev = get_version_from_git_show(path=path)
        except (CalledProcessError, KeyError, Version3Error):
            run_bump_my_version(Version3(0, 1, 0), path=path)
            return False
    current = get_version_from_path(path=path)
    patched = prev.bump_patch()
    if current in {patched, prev.bump_minor(), prev.bump_major()}:
        return True
    run_bump_my_version(patched)
    return False


if __name__ == "__main__":
    _main()
