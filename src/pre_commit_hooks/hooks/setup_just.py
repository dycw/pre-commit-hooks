from __future__ import annotations

from functools import partial
from re import MULTILINE, escape, search
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, normalize_multi_line_str

from pre_commit_hooks.constants import PYRIGHTCONFIG_JSON, paths_argument
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
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PYRIGHTCONFIG_JSON) -> bool:
    modifications: set[Path] = set()
    with yield_text_file(path, modifications=modifications) as context:
        text = normalize_multi_line_str("""
            set dotenv-load := true
            set fallback := true
            set positional-arguments := true
        """)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
