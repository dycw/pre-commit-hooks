from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import utilities.click
from click import argument, command
from loguru import logger
from more_itertools import chunked
from utilities.atomicwrites import writer

from pre_commit_hooks.common import run_every_option, throttled_run

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from whenever import DateTimeDelta


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
@run_every_option
def main(*, paths: tuple[Path, ...], run_every: DateTimeDelta | None = None) -> bool:
    """CLI for the `format-requirements` hook."""
    return throttled_run("mirror-files", run_every, _process, paths)


def _process(paths: Iterable[Path], /) -> bool:
    paths = list(paths)
    if len(paths) % 2 == 1:
        logger.exception(f"Expected an even number of paths; got {len(paths)}")
        raise RuntimeError
    results = list(map(_process_pair, chunked(paths, 2, strict=True)))  # run all
    return all(results)


def _process_pair(paths: Iterable[Path], /) -> bool:
    path_from, path_to = paths
    try:
        text_from = path_from.read_text()
    except FileNotFoundError:
        logger.exception(f"Source file {str(path_from)!r} not found")
        raise
    try:
        text_to = path_to.read_text()
    except FileNotFoundError:
        return _write_text(text_from, path_to)
    return True if text_from == text_to else _write_text(text_from, path_to)


def _write_text(text: str, path: Path, /) -> Literal[False]:
    with writer(path, overwrite=True) as temp:
        _ = temp.write_text(text)
    return False


__all__ = ["main"]
