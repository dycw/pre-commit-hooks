from __future__ import annotations

from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML, paths_argument
from pre_commit_hooks.utilities import (
    get_list_dicts,
    run_all_maybe_raise,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from utilities.types import PathLike


_HOOK_KEYS = [
    "id",
    "alias",
    "name",
    "language_version",
    "files",
    "exclude",
    "types",
    "types_or",
    "exclude_types",
    "args",
    "stages",
    "additional_dependencies",
    "always_run",
    "verbose",
    "log_file",
    "priority",
]


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))


def _run(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    path = Path(path)
    current = path.read_text()
    with yield_yaml_dict(path, sort_keys=False) as dict_:
        repos_list = get_list_dicts(dict_, "repos")
        repos_list.sort(key=lambda x: (x["repo"], x["rev"], x["hooks"]))
        for repo_dict in repos_list:
            hooks_list = get_list_dicts(repo_dict, "hooks")
            hooks_list.sort(key=lambda x: x["id"])
            for hook_dict in hooks_list:
                copy = hook_dict.copy()
                hook_dict.clear()
                for key in _HOOK_KEYS:
                    with suppress(KeyError):
                        hook_dict[key] = copy[key]
    return path.read_text() == current


if __name__ == "__main__":
    _main()
