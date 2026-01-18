from __future__ import annotations

from functools import partial
from re import search
from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from loguru import logger
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.pathlib import get_repo_root
from utilities.subprocess import run

from pre_commit_hooks.constants import BUMPVERSION_TOML
from pre_commit_hooks.utilities import get_version_from_path, run_all_maybe_raise


@command(**CONTEXT_SETTINGS)
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main() -> bool:
    if is_pytest():
        return None
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))
    if search("template", str(get_repo_root())):
        return True
    try:
        return _process(mode=mode)
    except RunBumpMyVersionError as error:
        logger.exception("%s", error.args[0])
        return False


def _process(*, mode: Mode = DEFAULT_MODE) -> bool:
    try:
        current = get_version_zz(mode)
    except GetVersionError as error:
        msg = f"Failed to bump version; error getting current verison: {error.args[0]}"
        raise RunBumpMyVersionError(msg) from None
    commit = check_output(["git", "rev-parse", "origin/master"], text=True).rstrip("\n")
    path = get_toml_path(mode)
    contents = check_output(["git", "show", f"{commit}:{path}"], text=True)
    try:
        master = get_version_zz(contents)
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


if __name__ == "__main__":
    _main()
