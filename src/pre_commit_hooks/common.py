from __future__ import annotations

from pathlib import Path
from typing import assert_never

from loguru import logger
from tomlkit import TOMLDocument, parse
from tomlkit.items import Table
from utilities.pathlib import get_repo_root
from utilities.version import Version, parse_version

PYPROJECT_TOML = get_repo_root().joinpath("pyproject.toml")


def get_version(
    path_or_text: Path | str | bytes | TOMLDocument, /, *, desc: str = ""
) -> Version:
    """Parse the version from a block of text."""
    match path_or_text:
        case Path() as path:
            return get_version(
                path.read_text(), desc=f" from {str(path)!r}" if desc == "" else desc
            )
        case str() | bytes() as text:
            return get_version(parse(text), desc=desc)
        case TOMLDocument() as doc:
            try:
                tool = doc["tool"]
            except KeyError:
                logger.exception(
                    f"Failed to get version{desc}; key 'tool' does not exist"
                )
                raise
            if not isinstance(tool, Table):
                logger.exception(f"Failed to get version{desc}; `tool` is not a Table")
                raise TypeError
            try:
                bumpversion = tool["bumpversion"]
            except KeyError:
                logger.exception(
                    f"Failed to get version{desc}; key 'bumpversion' does not exist"
                )
                raise
            if not isinstance(bumpversion, Table):
                logger.exception(
                    f"Failed to get version{desc}; `bumpversion` is not a Table"
                )
                raise TypeError
            try:
                version = bumpversion["current_version"]
            except KeyError:
                logger.exception(
                    f"Failed to get version{desc}; key 'current_version' does not exist"
                )
                raise
            if not isinstance(version, str):
                logger.exception(
                    f"Failed to get version{desc}; `version` is not a string"
                )
                raise TypeError
            return parse_version(version)
        case never:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(never)


__all__ = ["PYPROJECT_TOML", "get_version"]
