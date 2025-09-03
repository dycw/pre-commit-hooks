from __future__ import annotations

from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output

from click import command
from loguru import logger

from pre_commit_hooks.common import (
    DEFAULT_MODE,
    GetVersionError,
    Mode,
    get_toml_path,
    get_version,
    mode_option,
)


@command()
@mode_option
def main(*, mode: Mode = DEFAULT_MODE) -> bool:
    """CLI for the `run-bump-my-version` hook."""
    try:
        return _process(mode=mode)
    except RunBumpMyVersionError as error:
        logger.exception("%s", error.args[0])
        return False


def _process(*, mode: Mode = DEFAULT_MODE) -> bool:
    try:
        current = get_version(mode)
    except GetVersionError as error:
        msg = f"Failed to bump version; error getting current verison: {error.args[0]}"
        raise RunBumpMyVersionError(msg) from None
    commit = check_output(["git", "rev-parse", "origin/master"], text=True).rstrip("\n")
    path = get_toml_path(mode)
    contents = check_output(["git", "show", f"{commit}:{path}"], text=True)
    try:
        master = get_version(contents)
    except GetVersionError as error:
        msg = f"Failed to bump version; error getting master verison: {error.args[0]}"
        raise RunBumpMyVersionError(msg) from None
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
        msg = f"Failed to bump version; error running `bump-my-version`: {error.stderr.strip()}"
        raise GetVersionError(msg) from None
    except FileNotFoundError:
        msg = "Failed to bump version; is `bump-my-version` installed?"
        raise RunBumpMyVersionError(msg) from None
    else:
        return True


class RunBumpMyVersionError(Exception): ...


__all__ = ["main"]
