from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, read_text
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    DYCW_PRE_COMMIT_HOOKS_URL,
    PRE_COMMIT_CONFIG_REPO_KEYS,
    PYTEST_TOML,
    STD_PRE_COMMIT_HOOKS_URL,
    paths_argument,
)
from pre_commit_hooks.utilities import (
    get_list_dicts,
    merge_paths,
    re_insert_dict,
    re_insert_hook_dict,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, PathLike, StrMapping


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYTEST_TOML)
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths_use))


def _run(
    *, path: PathLike = PYTEST_TOML, skip_sort_args: MaybeSequenceStr | None = None
) -> bool:
    init = read_text(path)
    with yield_toml_doc(path) as doc:
        repos = get_list_dicts(doc, "repos")
        repos.sort(key=_sort_repos)
        for repo in repos:
            re_insert_dict(repo, PRE_COMMIT_CONFIG_REPO_KEYS)
            hooks = get_list_dicts(repo, "hooks")
            hooks.sort(key=_sort_hooks)
            for hook in hooks:
                re_insert_hook_dict(hook, repo, skip_sort_args=skip_sort_args)
    return read_text(path) == init


def _sort_repos(mapping: StrMapping, /) -> tuple[int, str, str]:
    repo = mapping["repo"]
    if repo == DYCW_PRE_COMMIT_HOOKS_URL:
        group = 0
    elif (repo != STD_PRE_COMMIT_HOOKS_URL) and ("pre-commit-hooks" in repo):
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
