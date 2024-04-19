from __future__ import annotations

from dataclasses import dataclass
from hashlib import md5
from pathlib import Path
from re import MULTILINE, findall
from subprocess import check_output
from typing import Literal

from loguru import logger
from semver import VersionInfo
from tomlkit import TOMLDocument, parse
from utilities.git import get_repo_root
from xdg_base_dirs import xdg_cache_home

_ROOT = get_repo_root()
PYPROJECT_TOML = _ROOT.joinpath("pyproject.toml")
REQUIREMENTS_TXT = _ROOT.joinpath("requirements.txt")


def check_versions(
    path: Path,
    pattern: str,
    /,
    *,
    name: Literal["run-bump2version", "run-hatch-version"],
) -> VersionInfo | None:
    """Check the versions: current & master.

    If the current is a correct bumping of master, then return `None`. Else,
    return the patch-bumped master.
    """
    with path.open() as fh:
        current = _parse_version(pattern, fh.read())
    master = _get_master_version(path, pattern, name=name)
    patched = master.bump_patch()
    if current in {master.bump_major(), master.bump_minor(), patched}:
        return None
    return patched


def _parse_version(pattern: str, text: str, /) -> VersionInfo:
    """Parse the version from a block of text."""
    (match,) = findall(pattern, text, flags=MULTILINE)
    return VersionInfo.parse(match)


def _get_master_version(
    path: Path,
    pattern: str,
    /,
    *,
    name: Literal["run-bump2version", "run-hatch-version"],
) -> VersionInfo:
    repo = md5(Path.cwd().as_posix().encode(), usedforsecurity=False).hexdigest()
    commit = check_output(["git", "rev-parse", "origin/master"], text=True).rstrip("\n")
    cache = xdg_cache_home().joinpath("pre-commit-hooks", name, repo, commit)
    try:
        with cache.open() as fh:
            return VersionInfo.parse(fh.read())
    except FileNotFoundError:
        cache.parent.mkdir(parents=True, exist_ok=True)
        text = check_output(["git", "show", f"{commit}:{path}"], text=True)
        version = _parse_version(pattern, text)
        with cache.open(mode="w") as fh:
            _ = fh.write(str(version))
        return version


@dataclass
class PyProject:
    contents: str
    doc: TOMLDocument


def read_pyproject() -> PyProject:
    try:
        with PYPROJECT_TOML.open(mode="r") as fh:
            contents = fh.read()
    except FileNotFoundError:
        logger.exception("pyproject.toml not found")
        raise
    doc = parse(contents)
    return PyProject(contents=contents, doc=doc)
