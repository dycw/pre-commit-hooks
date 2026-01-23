from __future__ import annotations

from functools import partial
from pathlib import Path
from re import MULTILINE, escape, search
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, read_text
from utilities.importlib import files

from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    GITATTRIBUTES,
    GITIGNORE,
    paths_argument,
    python_option,
)
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise, yield_text_file

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_option
def _main(*, paths: tuple[Path, ...], python: bool = False) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = []
    paths_use1 = merge_paths(*paths, target=GITATTRIBUTES, also_ok=GITIGNORE)
    funcs.extend([
        partial(_run_gitattributes, path=p, bumpversion=p.parent / BUMPVERSION_TOML)
        for p in paths_use1
    ])
    paths_use2 = merge_paths(*paths, target=GITIGNORE, also_ok=GITATTRIBUTES)
    funcs.extend([partial(_run_gitignore, path=p, python=python) for p in paths_use2])
    run_all_maybe_raise(*funcs)


def _run_gitattributes(
    *, path: PathLike = GITATTRIBUTES, bumpversion: PathLike = BUMPVERSION_TOML
) -> bool:
    modifications: set[Path] = set()
    with yield_text_file(path, modifications=modifications) as context:
        text = f"{bumpversion} linguist-generated=true"
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n{text}"
    return len(modifications) == 0


def _run_gitignore(*, path: PathLike = GITIGNORE, python: bool = False) -> bool:
    modifications: set[Path] = set()
    with yield_text_file(path, modifications=modifications) as context:
        text = _get_text(python=python)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n{text}"
    return len(modifications) == 0


def _get_text(*, python: bool = False) -> str:
    configs = files(anchor="pre_commit_hooks") / "configs"
    lines: list[str] = [read_text(configs / "gitignore-generic")]
    if python:
        lines.append(read_text(configs / "gitignore-python"))
    return "\n\n".join(lines)


if __name__ == "__main__":
    _main()
