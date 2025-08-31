from __future__ import annotations

from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output

from click import command
from loguru import logger

from pre_commit_hooks.common import (
    DEFAULT_MODE,
    Mode,
    get_toml_path,
    get_version,
    mode_option,
)


@command()
@mode_option
def main(*, mode: Mode = DEFAULT_MODE) -> bool:
    """CLI for the `run-bump-my-version` hook."""
    return _process(mode=mode)


def _process(*, mode: Mode = DEFAULT_MODE) -> bool:
    current = get_version(mode)
    commit = check_output(["git", "rev-parse", "origin/master"], text=True).rstrip("\n")
    path = get_toml_path(mode)
    contents = check_output(["git", "show", f"{commit}:{path}"], text=True)
    master = get_version(contents)
    if current in {master.bump_patch(), master.bump_minor(), master.bump_major()}:
        return True
    cmd = [
        "bump-my-version",
        "replace",
        "--new-version",
        str(master.bump_patch()),
        str(path),
    ]
    try:
        _ = check_call(cmd, stdout=PIPE, stderr=STDOUT)
    except CalledProcessError as error:
        if error.returncode != 1:
            logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
    except FileNotFoundError:
        logger.exception(
            "Failed to run {cmd!r}. Is `bump-my-version` installed?", cmd=" ".join(cmd)
        )
    else:
        return True
    return False


__all__ = ["main"]
