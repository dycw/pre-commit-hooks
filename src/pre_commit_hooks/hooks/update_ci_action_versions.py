from __future__ import annotations

from functools import partial
from re import MULTILINE, sub
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest

from pre_commit_hooks.constants import paths_argument
from pre_commit_hooks.utilities import run_all_maybe_raise, yield_text_file

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p) for p in paths))


def _run(path: PathLike, /) -> bool:
    modifications: set[Path] = set()
    versions = {
        "actions/checkout": "v6",
        "actions/setup-python": "v6",
        "astral-sh/ruff-action": "v3",
        "astral-sh/setup-uv": "v7",
    }
    with yield_text_file(path, modifications=modifications) as context:
        text = context.input
        for action, version in versions.items():
            text = sub(
                rf"^(\s*- uses: {action})@.+$", rf"\1@{version}", text, flags=MULTILINE
            )
        context.output = text
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
