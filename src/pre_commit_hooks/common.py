from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, assert_never

import utilities.click
from click import Choice, option
from loguru import logger
from tomlkit import TOMLDocument, parse
from tomlkit.items import Table
from utilities.atomicwrites import writer
from utilities.hashlib import md5_hash
from utilities.pathlib import get_repo_root
from utilities.typing import get_literal_elements
from utilities.version import Version, parse_version
from utilities.whenever import get_now_local, to_zoned_date_time
from xdg_base_dirs import xdg_cache_home

if TYPE_CHECKING:
    from collections.abc import Callable

    from whenever import DateTimeDelta

type Mode = Literal["pyproject", "bumpversion"]
DEFAULT_MODE: Mode = "pyproject"
mode_option = option(
    "--mode",
    type=Choice(get_literal_elements(Mode), case_sensitive=False),
    default=DEFAULT_MODE,
    show_default=True,
)
run_every_option = option(
    "--run-every", type=utilities.click.DateTimeDelta(), default=None, show_default=True
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
    """Get the path of the TOML file with the version."""
    match mode:
        case "pyproject":
            return Path("pyproject.toml")
        case "bumpversion":
            return Path(".bumpversion.toml")
        case never:  # pyright: ignore[reportUnnecessaryComparison]
            assert_never(never)


def throttled_run[**P](
    name: str,
    run_every: DateTimeDelta | None,
    func: Callable[P, bool],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> bool:
    """Throttled run."""
    hash_ = md5_hash(get_repo_root())
    path = xdg_cache_home().joinpath(name, hash_)
    if run_every is not None:
        min_date_time = get_now_local() - run_every
        try:
            text = path.read_text()
        except FileNotFoundError:
            pass
        else:
            try:
                last_run = to_zoned_date_time(text.strip("\n"))
            except ValueError:
                pass
            else:
                if min_date_time <= last_run:
                    return True
    try:
        return func(*args, **kwargs)
    finally:
        with writer(path, overwrite=True) as temp:
            _ = temp.write_text(str(get_now_local()))


__all__ = [
    "DEFAULT_MODE",
    "Mode",
    "get_toml_path",
    "get_version",
    "mode_option",
    "run_every_option",
    "throttled_run",
]
