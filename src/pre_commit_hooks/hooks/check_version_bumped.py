from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.subprocess import run

from pre_commit_hooks.constants import BUMPVERSION_TOML
from pre_commit_hooks.utilities import (
    get_version_from_path,
    get_version_origin_master,
    run_all_maybe_raise,
)

if TYPE_CHECKING:
    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
def _main() -> None:
    if is_pytest():
        return
    run_all_maybe_raise(_run)


def _run(*, path: PathLike = BUMPVERSION_TOML) -> bool:
    curr_sha = _get_sha("HEAD")
    prev_sha = _get_sha("origin/master")
    if curr_sha == prev_sha:
        return True
    try:
        curr_version = get_version_from_path(path=path)
        prev_version = get_version_origin_master(path=path)
    except ValueError:
        return False
    return curr_version != prev_version


def _get_sha(commit: str, /) -> str:
    return run("git", "rev-parse", commit, return_=True)


if __name__ == "__main__":
    _main()
