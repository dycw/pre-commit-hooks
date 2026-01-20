from __future__ import annotations

from functools import partial
from pathlib import Path
from re import MULTILINE, escape, search
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.iterables import always_iterable
from utilities.os import is_pytest
from utilities.text import strip_and_dedent
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    ENVRC,
    PYTHON_VERSION,
    certificates_option,
    paths_argument,
    python_option,
    python_uv_index_option,
    python_version_option,
)
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise, yield_text_file

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_option
@python_uv_index_option
@certificates_option
@python_version_option
def _main(
    *,
    paths: tuple[Path, ...],
    python: bool = False,
    python_uv_index: MaybeSequenceStr | None = None,
    certificates: bool = False,
    python_version: str | None = None,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=ENVRC)
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            python=python,
            uv_index=python_uv_index,
            uv_native_tls=certificates,
            version=python_version,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = ENVRC,
    python: bool = False,
    uv_index: MaybeSequenceStr | None = None,
    uv_native_tls: bool = False,
    version: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    with yield_text_file(path, modifications=modifications) as context:
        text = strip_and_dedent("""
            #!/usr/bin/env sh
            # shellcheck source=/dev/null

            # echo
            echo_date() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2; }
        """)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"
    if python:
        _add_python(
            path=path,
            modifications=modifications,
            uv_index=uv_index,
            uv_native_tls=uv_native_tls,
            version=version,
        )
    return len(modifications) == 0


def _add_python(
    *,
    path: PathLike = ENVRC,
    modifications: MutableSet[Path] | None = None,
    uv_index: MaybeSequenceStr | None = None,
    uv_native_tls: bool = False,
    version: str | None = None,
) -> None:
    with yield_text_file(path, modifications=modifications) as context:
        text = _get_text(
            uv_index=uv_index, uv_native_tls=uv_native_tls, version=version
        )
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"


def _get_text(
    *,
    uv_index: MaybeSequenceStr | None = None,
    uv_native_tls: bool = False,
    version: str | None = None,
) -> str:
    lines: list[str] = ["# uv"]
    if uv_index is not None:
        lines.append(f"export UV_INDEX='{','.join(always_iterable(uv_index))}'")
    lines.append("export UV_MANAGED_PYTHON='true'")
    if uv_native_tls:
        lines.append("export UV_NATIVE_TLS='true'")
    version_use = PYTHON_VERSION if version is None else version
    lines.extend([
        "export UV_PRERELEASE='disallow'",
        f"export UV_PYTHON='{version_use}'",
        "export UV_RESOLUTION='highest'",
        "export UV_VENV_CLEAR=1",
        strip_and_dedent("""\
            if ! command -v uv >/dev/null 2>&1; then
            \techo_date "ERROR: 'uv' not found" && exit 1
            fi
        """),
        "activate='.venv/bin/activate'",
        strip_and_dedent("""\
            if [ -f $activate ]; then
            \t. $activate
            else
            \tuv venv
            fi
        """),
        "uv sync --all-extras --all-groups --active --locked",
    ])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    _main()
