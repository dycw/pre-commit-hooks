from __future__ import annotations

from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    PRE_COMMIT_CONFIG_HOOK_KEYS,
    PRE_COMMIT_CONFIG_REPO_KEYS,
    PRE_COMMIT_CONFIG_YAML,
    PRE_COMMIT_HOOKS_HOOK_KEYS,
    paths_argument,
)
from pre_commit_hooks.utilities import (
    get_list_dicts,
    run_all_maybe_raise,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from utilities.types import PathLike, StrDict, StrMapping


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
        repos_list.sort(key=_sort_key)
        for repo_dict in repos_list:
            _re_insert_dict(repo_dict, PRE_COMMIT_CONFIG_REPO_KEYS)
            hooks_list = get_list_dicts(repo_dict, "hooks")
            hooks_list.sort(key=lambda x: x["id"])
            if repo_dict["repo"] == "local":
                keys = PRE_COMMIT_HOOKS_HOOK_KEYS
            else:
                keys = PRE_COMMIT_CONFIG_HOOK_KEYS
            for hook_dict in hooks_list:
                _re_insert_dict(hook_dict, keys)
        repos_list.append({"DUMMY": "DUMMY"})
    with yield_yaml_dict(path, sort_keys=False) as dict_:
        repos_list = get_list_dicts(dict_, "repos")
        _ = repos_list.pop(-1)
    return path.read_text() == current


def _re_insert_dict(dict_: StrDict, keys: list[str], /) -> None:
    copy = dict_.copy()
    dict_.clear()
    for key in keys:
        with suppress(KeyError):
            dict_[key] = copy[key]


def _sort_key(mapping: StrMapping, /) -> tuple[str, str]:
    return mapping["repo"], mapping.get("rev", "")


if __name__ == "__main__":
    _main()
