from __future__ import annotations

from subprocess import PIPE, STDOUT, CalledProcessError, check_call

from click import command
from loguru import logger

from pre_commit_hooks.common import PYPROJECT_TOML, check_versions


@command()
def main() -> bool:
    """CLI for the `run_bump_my_version` hook."""
    return _process()


def _process() -> bool:
    pattern = r"current_version = (\d+\.\d+\.\d+)$"
    version = check_versions(PYPROJECT_TOML, pattern, "run-bump-my-version")
    if version is None:
        return True
    cmd = ["bump-my-version", "--allow-dirty", f"--new-version={version}", "patch"]
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
