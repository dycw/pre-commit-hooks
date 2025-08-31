from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from loguru import logger
from more_itertools import chunked
from utilities.atomicwrites import writer

if TYPE_CHECKING:
    from pathlib import Path


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
def main(*, paths: tuple[Path, ...]) -> bool:
    """CLI for the `format-requirements` hook."""
    if len(paths) % 2 == 1:
        logger.exception(f"Expected an even number of paths; got {len(paths)}")
        raise RuntimeError
    results = list(map(_process, chunked(paths, 2, strict=True)))  # run all
    return all(results)


def _process(paths: list[Path], /) -> bool:
    text_from, text_to = [p.read_text() for p in paths]
    if text_from == text_to:
        return True
    _, path_to = paths
    with writer(path_to, overwrite=True) as temp:
        _ = temp.write_text(text_from)
    return False


__all__ = ["main"]
