from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest

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
    try:
        current = get_version_from_path(path=path)
        prev = get_version_origin_master(path=path)
    except ValueError:
        return False
    return current != prev


if __name__ == "__main__":
    _main()
