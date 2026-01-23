from __future__ import annotations

from functools import partial
from re import MULTILINE, escape, search
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest

from pre_commit_hooks.constants import (
    README_MD,
    description_option,
    paths_argument,
    repo_name_option,
)
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise, yield_text_file

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@repo_name_option
@description_option
def _main(
    *,
    paths: tuple[Path, ...],
    repo_name: str | None = None,
    description: str | None = None,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=README_MD)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, repo_name=repo_name, description=description)
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = README_MD,
    repo_name: str | None = None,
    description: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    if (repo_name is not None) and (description is not None):
        _add_header(repo_name, description, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_header(
    repo_name: str,
    description: str,
    path: PathLike = README_MD,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_text_file(path, modifications=modifications) as context:
        lines = [f"# `{repo_name}`", description]
        text = "\n\n".join(lines)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"


if __name__ == "__main__":
    _main()
