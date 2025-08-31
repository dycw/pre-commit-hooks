from __future__ import annotations

from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output
from typing import Literal, assert_never

from click import Choice, command, option
from loguru import logger
from utilities.pathlib import get_repo_root

from pre_commit_hooks.common import PYPROJECT_TOML, get_version

type _Mode = Literal["pyproject", "bumpversion"]
_MODE: _Mode = "pyproject"


@command()
@option(
    "--mode",
    type=Choice(["pyproject", "bumpversion"], case_sensitive=False),
    default=_MODE,
    show_default=True,
)
def main(*, mode: _Mode = _MODE) -> bool:
    """CLI for the `run_bump_my_version` hook."""
    return _process(mode=mode)


def _process(*, mode: _Mode = _MODE) -> bool:
    path = _get_rel_path(mode=mode)
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


def _get_rel_path(*, mode: _Mode = _MODE) -> Path:
    match mode:
        case "pyproject":
            path = PYPROJECT_TOML
        case "bumpversion":
            path = get_repo_root().joinpath(".bumpversion.toml")
        case never:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(never)
    return path.relative_to(Path.cwd())


__all__ = ["main"]
