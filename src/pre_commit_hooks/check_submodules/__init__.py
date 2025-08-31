from __future__ import annotations

from click import command

from pre_commit_hooks.common import (
    DEFAULT_MODE,
    Mode,
    get_toml_path,
    get_version,
    mode_option,
)


@command()
def main() -> bool:
    """CLI for the `check-submodules` hook."""
    return _process(mode=mode)


def _process() -> None:
    pass


__all__ = [
    "DEFAULT_MODE",
    "Mode",
    "get_toml_path",
    "get_version",
    "main",
    "mode_option",
]
