from __future__ import annotations

from functools import partial
from pathlib import Path
from re import MULTILINE, escape, search
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.importlib import files
from utilities.os import is_pytest

from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    GITATTRIBUTES,
    GITIGNORE,
    paths_argument,
)
from pre_commit_hooks.utilities import run_all_maybe_raise, yield_text_file

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            attributes=p.parent / GITATTRIBUTES,
            bumpversion=p.parent / BUMPVERSION_TOML,
            ignore=p.parent / GITIGNORE,
        )
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    attributes: PathLike = GITATTRIBUTES,
    bumpversion: PathLike = BUMPVERSION_TOML,
    ignore: PathLike = GITIGNORE,
) -> bool:
    modifications: set[Path] = set()
    with yield_text_file(attributes, modifications=modifications) as context:
        text = f"{bumpversion} linguist-generated=true"
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n{text}"
    with yield_text_file(ignore, modifications=modifications) as context:
        text = (files(anchor="pre_commit_hooks") / "configs/gitignore").read_text()
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
