from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, check_call
from typing import cast

from beartype import beartype
from click import command
from git import Repo
from loguru import logger
from tomlkit import loads
from tomlkit.container import Container

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
            logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
    except FileNotFoundError:
        logger.exception(
            "Failed to run {cmd!r}. Is `hatch` installed?", cmd=" ".join(cmd)
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
        doc = loads(fh.read())
    try:
        tool = cast(Container, doc["tool"])
    except KeyError:
        logger.exception('pyproject.toml has no "tool" section')
        raise
    try:
        hatch = cast(Container, tool["hatch"])
    except KeyError:
        logger.exception('pyproject.toml has no "tool.hatch" section')
        raise
    try:
        version = cast(Container, hatch["version"])
    except KeyError:
        logger.exception('pyproject.toml has no "tool.hatch.version" section')
        raise
    return Path(cast(str, version["path"]))
