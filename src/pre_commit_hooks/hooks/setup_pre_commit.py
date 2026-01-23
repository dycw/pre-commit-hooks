from __future__ import annotations

from contextlib import suppress
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    DYCW_PRE_COMMIT_HOOKS_URL,
    PRE_COMMIT_CONFIG_YAML,
    PRE_COMMIT_PRIORITY,
    paths_argument,
)
from pre_commit_hooks.utilities import (
    get_list_strs,
    get_set_list_dicts,
    get_set_partial_dict,
    run_all_maybe_raise,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos = get_set_list_dicts(dict_, "repos")
        repo = get_set_partial_dict(repos, {"repo": DYCW_PRE_COMMIT_HOOKS_URL})
        hooks = get_set_list_dicts(repo, "hooks")
        hook = get_set_partial_dict(hooks, {"id": "add-hooks"})
        with suppress(KeyError):
            args = get_list_strs(hook, "args")
            args.sort()
        hook["priority"] = PRE_COMMIT_PRIORITY
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
