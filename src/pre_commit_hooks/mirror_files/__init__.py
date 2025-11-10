from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from loguru import logger

from pre_commit_hooks.common import (
    ProcessInPairsError,
    process_in_pairs,
    run_all,
    run_every_option,
    throttled_run,
    write_text,
)

if TYPE_CHECKING:
    from pathlib import Path

    from whenever import DateTimeDelta


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
@run_every_option
def main(*, paths: tuple[Path, ...], run_every: DateTimeDelta | None = None) -> bool:
    """CLI for the `mirror-files` hook."""
    try:
        return throttled_run(
            "mirror-files", run_every, process_in_pairs, paths, _process_pair
        )
    except (ProcessInPairsError, MirrorFilesError) as error:
        logger.exception("%s", error.args[0])
        return False


def _process_pair(path_from: Path, path_to: Path, /) -> bool:
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


__all__ = ["main", "run_all"]
