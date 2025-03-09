from __future__ import annotations

import re
from pathlib import Path
from re import MULTILINE
from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output

from click import command
from loguru import logger
from utilities.version import Version, parse_version

from pre_commit_hooks.common import PYPROJECT_TOML


@command()
def main() -> bool:
    """CLI for the `run_bump_my_version` hook."""
    return _process()


def _process() -> bool:
    path = PYPROJECT_TOML.relative_to(Path.cwd())
    current = _parse_version_from_file_or_text(path)
    commit = check_output(["git", "rev-parse", "origin/master"], text=True).rstrip("\n")
    contents = check_output(["git", "show", f"{commit}:{path}"], text=True)
    master = _parse_version_from_file_or_text(contents)
    if current in {master.bump_patch(), master.bump_minor(), master.bump_major()}:
        return True
    cmd = ["bump-my-version", "bump", "patch"]
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


_PATTERN = re.compile(r'^current_version = "(\d+\.\d+\.\d+)"$', flags=MULTILINE)


def _parse_version_from_file_or_text(path_or_text: Path | str, /) -> Version:
    """Parse the version from a block of text."""
    match path_or_text:
        case Path() as path:
            with path.open() as fh:
                return _parse_version_from_file_or_text(fh.read())
        case str() as text:
            (match,) = _PATTERN.findall(text)
            return parse_version(match)
