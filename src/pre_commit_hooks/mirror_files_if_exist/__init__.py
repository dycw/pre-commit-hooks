from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from loguru import logger

from pre_commit_hooks.common import (
    CopySourceToTargetSourceError,
    CopySourceToTargetTargetError,
    ProcessInPairsError,
    copy_source_to_target,
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
    """CLI for the `mirror-files-if-exist` hook."""
    try:
        return throttled_run(
            "mirror-files-if-exist", run_every, process_in_pairs, paths, _process_pair
        )
    except (ProcessInPairsError, MirrorFilesIfExistError) as error:
        logger.exception("%s", error.args[0])
        return False


def _process_pair(path_from: Path, path_to: Path, /) -> bool:
    try:
        return copy_source_to_target(path_from, path_to, error_if_missing=True)
    except CopySourceToTargetSourceError as error:
        raise MirrorFilesIfExistError(error.args[0]) from None
    except CopySourceToTargetTargetError:
        return True


class MirrorFilesIfExistError(Exception): ...


__all__ = ["main", "run_all", "write_text"]
