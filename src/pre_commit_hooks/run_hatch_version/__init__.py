from pathlib import Path
from subprocess import (
    PIPE,
    STDOUT,
    CalledProcessError,
    check_call,
)

from beartype import beartype
from click import command
from git import Repo
from loguru import logger
from tomli import loads

from pre_commit_hooks.common import check_versions


@command()
@beartype
def main() -> bool:
    """CLI for the `run-hatch-version` hook."""
    return _process()


@beartype
def _process() -> bool:
    path = _get_path_version_file()
    pattern = r'^__version__ = "(\d+\.\d+\.\d+)"$'
    version = check_versions(path, pattern, name="run-hatch-version")
    if version is None:
        return True
    cmd = ["hatch", "version", str(version)]
    try:
        _ = check_call(cmd, stdout=PIPE, stderr=STDOUT)
    except CalledProcessError as error:
        if error.returncode != 1:
            logger.exception("Failed to run {!r}", " ".join(cmd))
    except FileNotFoundError:
        logger.exception(
            "Failed to run {!r}. Is `hatch` installed?",
            " ".join(cmd),
        )
    else:
        return True
    return False


@beartype
def _get_path_version_file() -> Path:
    repo = Repo(".", search_parent_directories=True)
    if (wtd := repo.working_tree_dir) is None:
        raise ValueError(str(repo))
    with Path(wtd, "pyproject.toml").open() as fh:
        config = loads(fh.read())
    return Path(config["tool"]["hatch"]["version"]["path"])
