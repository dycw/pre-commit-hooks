from __future__ import annotations

from dataclasses import dataclass

from loguru import logger
from tomlkit import TOMLDocument, parse
from utilities.git import get_repo_root

_ROOT = get_repo_root()
PYPROJECT_TOML = _ROOT.joinpath("pyproject.toml")


##


@dataclass(kw_only=True)
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


__all__ = ["PYPROJECT_TOML", "read_pyproject"]
