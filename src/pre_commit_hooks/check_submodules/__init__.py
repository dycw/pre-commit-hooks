from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from git import Repo, Submodule

from pre_commit_hooks.common import (
    DEFAULT_MODE,
    Mode,
    get_toml_path,
    get_version,
    mode_option,
    run_every_option,
    throttled_run,
)

if TYPE_CHECKING:
    from whenever import DateTimeDelta


@command()
@run_every_option
def main(*, run_every: DateTimeDelta | None = None) -> bool:
    """CLI for the `check-submodules` hook."""
    return throttled_run("check-submodules", run_every, _process)


def _process() -> bool:
    repo = Repo(".", search_parent_directories=True)
    results = [_process_submodule(s) for s in repo.submodules]  # run all
    return all(results)


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
