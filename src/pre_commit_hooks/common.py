from __future__ import annotations

from pathlib import Path
from typing import assert_never

from loguru import logger
from tomlkit import TOMLDocument, parse
from tomlkit.items import Table
from utilities.pathlib import get_repo_root
from utilities.version import Version, parse_version

PYPROJECT_TOML = get_repo_root().joinpath("pyproject.toml")


def get_version(source: Path | str | bytes | TOMLDocument, /) -> Version:
    """Get the `[tool.bumpversion]` version from a TOML file."""
    match source:
        case Path() as path:
            return get_version(path.read_text())
        case str() | bytes() as text:
            return get_version(parse(text))
        case TOMLDocument() as doc:
            try:
                tool = doc["tool"]
            except KeyError:
                logger.exception("Failed to get version; key 'tool' does not exist")
                raise
            if not isinstance(tool, Table):
                logger.exception("Failed to get version; `tool` is not a Table")
                raise TypeError
            try:
                bumpversion = tool["bumpversion"]
            except KeyError:
                logger.exception(
                    "Failed to get version; key 'bumpversion' does not exist"
                )
                raise
            if not isinstance(bumpversion, Table):
                logger.exception("Failed to get version; `bumpversion` is not a Table")
                raise TypeError
            try:
                version = bumpversion["current_version"]
            except KeyError:
                logger.exception(
                    "Failed to get version; key 'current_version' does not exist"
                )
                raise
            if not isinstance(version, str):
                logger.exception("Failed to get version; `version` is not a string")
                raise TypeError
            return parse_version(version)
        case never:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(never)


__all__ = ["PYPROJECT_TOML", "get_version"]
