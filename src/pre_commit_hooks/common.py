from __future__ import annotations

from pathlib import Path
from typing import Literal, assert_never

from click import Choice, option
from loguru import logger
from tomlkit import TOMLDocument, parse
from tomlkit.items import Table
from utilities.pathlib import get_repo_root
from utilities.typing import get_literal_elements
from utilities.version import Version, parse_version

type Mode = Literal["pyproject", "bumpversion"]
DEFAULT_MODE: Mode = "pyproject"
mode_option = option(
    "--mode",
    type=Choice(get_literal_elements(Mode), case_sensitive=False),
    default=DEFAULT_MODE,
    show_default=True,
)


def get_version(source: Mode | Path | str | bytes | TOMLDocument, /) -> Version:
    """Get the `[tool.bumpversion]` version from a TOML file."""
    match source:
        case "pyproject" | "bumpversion" as mode:
            return get_version(get_toml_path(mode))
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


def get_toml_path(mode: Mode = DEFAULT_MODE, /) -> Path:
    root = get_repo_root()
    match mode:
        case "pyproject":
            filename = "pyproject.toml"
        case "bumpversion":
            filename = ".bumpversion.toml"
        case never:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(never)
    return root.relative_to(filename)


__all__ = ["DEFAULT_MODE", "Mode", "get_toml_path", "get_version", "mode_option"]
