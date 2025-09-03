from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from loguru import logger
from more_itertools import chunked

from pre_commit_hooks.common import run_all, run_every_option, throttled_run, write_text

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from whenever import DateTimeDelta


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
@run_every_option
def main(*, paths: tuple[Path, ...], run_every: DateTimeDelta | None = None) -> bool:
    """CLI for the `format-requirements` hook."""
    try:
        return throttled_run("mirror-files", run_every, _process, paths)
    except MirrorFilesError as error:
        logger.exception("%s", error.args[0])
        return False


def _process(paths: Iterable[Path], /) -> bool:
    paths = list(paths)
    if len(paths) % 2 == 1:
        msg = f"Expected an even number of paths; got {len(paths)}"
        raise MirrorFilesError(msg)
    return run_all(map(_process_pair, chunked(paths, 2, strict=True)))


def _process_pair(paths: Iterable[Path], /) -> bool:
    path_from, path_to = paths
    try:
        text_from = path_from.read_text()
    except FileNotFoundError:
        msg = f"Failed to mirror {str(path_from)!r}; path does not exist"
        raise MirrorFilesError(msg) from None
    try:
        text_to = path_to.read_text()
    except FileNotFoundError:
        return write_text(path_to, text_from)
    return True if text_from == text_to else write_text(path_to, text_from)


class MirrorFilesError(Exception): ...


__all__ = ["main"]
