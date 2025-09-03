from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from git import Repo, Submodule

from pre_commit_hooks.common import (
    DEFAULT_MODE,
    Mode,
    get_toml_path,
    get_version,
    mode_option,
    run_all,
    run_every_option,
    throttled_run,
)

if TYPE_CHECKING:
    from pathlib import Path

    from whenever import DateTimeDelta


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
@run_every_option
def main(*, paths: tuple[Path, ...], run_every: DateTimeDelta | None = None) -> bool:
    """CLI for the `check-submodules` hook."""
    return run_all(
        throttled_run("check-submodules", run_every, _process, p) for p in paths
    )


def _process(path: Path, /) -> bool:
    repo = Repo(path, search_parent_directories=True)
    return run_all(_process_submodule(s) for s in repo.submodules)


def _process_submodule(submodule: Submodule, /) -> bool:
    repo = submodule.module()
    _ = repo.remotes.origin.fetch()
    local = repo.commit("master")
    remote = repo.commit("origin/master")
    return local.hexsha == remote.hexsha


__all__ = [
    "DEFAULT_MODE",
    "Mode",
    "get_toml_path",
    "get_version",
    "main",
    "mode_option",
]
