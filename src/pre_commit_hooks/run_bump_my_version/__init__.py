from __future__ import annotations

from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output

from click import command
from loguru import logger

from pre_commit_hooks.common import PYPROJECT_TOML, get_version


@command()
def main() -> bool:
    """CLI for the `run_bump_my_version` hook."""
    return _process()


def _process() -> bool:
    path = PYPROJECT_TOML.relative_to(Path.cwd())
    current = get_version(path)
    commit = check_output(["git", "rev-parse", "origin/master"], text=True).rstrip("\n")
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
