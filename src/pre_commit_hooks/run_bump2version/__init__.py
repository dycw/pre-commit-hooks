from __future__ import annotations

from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, check_call
from typing import Literal

from click import command, option
from loguru import logger

from pre_commit_hooks.common import (
    PYPROJECT_TOML,
    check_versions,
    trim_trailing_whitespaces,
)


@command()
@option(
    "--setup-cfg", is_flag=True, help="Read `setup.cfg` instead of `bumpversion.cfg`"
)
def main(*, setup_cfg: bool) -> bool:
    """CLI for the `run_bump2version` hook."""
    filename = "setup.cfg" if setup_cfg else ".bumpversion.cfg"
    return _process(filename=filename)


def _process(*, filename: Literal["setup.cfg", ".bumpversion.cfg"]) -> bool:
    path = Path(filename)
    pattern = r"current_version = (\d+\.\d+\.\d+)$"
    version = check_versions(PYPROJECT_TOML, pattern, "run-bump2version")
    if version is None:
        return True
    cmd = ["bump2version", "--allow-dirty", f"--new-version={version}", "patch"]
    try:
        _ = check_call(cmd, stdout=PIPE, stderr=STDOUT)
    except CalledProcessError as error:
        if error.returncode != 1:
            logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
    except FileNotFoundError:
        logger.exception(
            "Failed to run {cmd!r}. Is `bump2version` installed?", cmd=" ".join(cmd)
        )
    else:
        trim_trailing_whitespaces(path)
        return True
    return False
