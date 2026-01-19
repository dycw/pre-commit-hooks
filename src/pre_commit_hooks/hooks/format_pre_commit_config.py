from __future__ import annotations

from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.constants import sentinel
from utilities.os import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    DYCW_PRE_COMMIT_HOOKS_URL,
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
    with yield_yaml_dict(path) as dict_:
        repos = get_list_dicts(dict_, "repos")
        repos.sort(key=_sort_repos)
        for repo in repos:
            _re_insert(repo, PRE_COMMIT_CONFIG_REPO_KEYS)
            hooks = get_list_dicts(repo, "hooks")
            hooks.sort(key=_sort_hooks)
            if repo["repo"] == "local":
                keys = PRE_COMMIT_HOOKS_HOOK_KEYS
            else:
                keys = PRE_COMMIT_CONFIG_HOOK_KEYS
            for hook in hooks:
                _re_insert(hook, keys)
        repos.append({"repo": str(sentinel)})
    with yield_yaml_dict(path) as dict_:
        repos = get_list_dicts(dict_, "repos")
        _ = repos.pop(-1)
    return path.read_text() == current


def _re_insert(dict_: StrDict, keys: list[str], /) -> None:
    copy = dict_.copy()
    dict_.clear()
    for key in keys:
        with suppress(KeyError):
            dict_[key] = copy[key]


def _sort_repos(mapping: StrMapping, /) -> tuple[int, str, str]:
    repo = mapping["repo"]
    if repo == DYCW_PRE_COMMIT_HOOKS_URL:
        group = 0
    elif "pre-commit-hooks" in repo:
        group = 1
    else:
        group = 2
    rev = mapping.get("rev", "")
    return group, repo, rev


def _sort_hooks(mapping: StrMapping, /) -> tuple[int, str]:
    id_ = mapping["id"]
    group = 0 if id_ == "add-hooks" else 1
    return group, id_


if __name__ == "__main__":
    _main()
