from __future__ import annotations

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.pathlib import get_repo_root
from utilities.version import Version3

from pre_commit_hooks.utilities import (
    get_version_from_path,
    get_version_origin_master,
    run_all_maybe_raise,
    set_version,
)


@command(**CONTEXT_SETTINGS)
def _main() -> None:
    if ("template" in str(get_repo_root())) or is_pytest():
        return
    run_all_maybe_raise(_run)


def _run() -> bool:
    try:
        prev = get_version_origin_master()
        current = get_version_from_path()
    except ValueError:
        set_version(Version3(0, 1, 0))
        return False
    patched = prev.bump_patch()
    if current in {patched, prev.bump_minor(), prev.bump_major()}:
        return True
    set_version(patched)
    return False


if __name__ == "__main__":
    _main()
