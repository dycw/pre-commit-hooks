from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.version import Version3

from pre_commit_hooks.constants import BUMPVERSION_TOML, paths_argument
from pre_commit_hooks.utilities import (
    get_version_from_path,
    get_version_origin_master,
    merge_paths,
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
    paths_use = merge_paths(*paths, target=BUMPVERSION_TOML)
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths_use))


def _run(*, path: PathLike = BUMPVERSION_TOML) -> bool:
    try:
        prev = get_version_origin_master(path=path)
        current = get_version_from_path(path=path)
    except ValueError:
        set_version(Version3(0, 1, 0), path=path)
        return False
    patched = prev.bump_patch()
    if current in {patched, prev.bump_minor(), prev.bump_major()}:
        return True
    set_version(patched, path=path)
    return False


if __name__ == "__main__":
    _main()
