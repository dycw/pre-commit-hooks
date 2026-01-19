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
    DEFAULT_PYTHON_VERSION,
    ENVRC,
    paths_argument,
    python_option,
    python_uv_index_option,
    python_uv_native_tls_option,
    python_version_option,
)
from pre_commit_hooks.utilities import run_all_maybe_raise, yield_text_file

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_option
@python_uv_index_option
@python_uv_native_tls_option
@python_version_option
def _main(
    *,
    paths: tuple[Path, ...],
    python: bool = False,
    python_uv_index: MaybeSequenceStr | None = None,
    python_uv_native_tls: bool = False,
    python_version: str = DEFAULT_PYTHON_VERSION,
) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(
        *(
            partial(
                _run,
                path=p.parent / ENVRC,
                python=python,
                python_uv_index=python_uv_index,
                python_uv_native_tls=python_uv_native_tls,
                python_version=python_version,
            )
            for p in paths
        )
    )


def _run(
    *,
    path: PathLike = ENVRC,
    python: bool = False,
    python_uv_index: MaybeSequenceStr | None = None,
    python_uv_native_tls: bool = False,
    python_version: str = DEFAULT_PYTHON_VERSION,
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
            uv_index=python_uv_index,
            uv_native_tls=python_uv_native_tls,
            version=python_version,
        )
    return len(modifications) == 0


def _add_python(
    *,
    path: PathLike = ENVRC,
    modifications: MutableSet[Path] | None = None,
    uv_index: MaybeSequenceStr | None = None,
    uv_native_tls: bool = False,
    version: str = DEFAULT_PYTHON_VERSION,
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
    version: str = DEFAULT_PYTHON_VERSION,
) -> str:
    lines: list[str] = ["# uv", "export UV_MANAGED_PYTHON='true'"]
    if uv_index is not None:
        lines.append(f"export UV_INDEX='{','.join(always_iterable(uv_index))}'")
    if uv_native_tls:
        lines.append("export UV_NATIVE_TLS='true'")
    lines.extend([
        "export UV_PRERELEASE='disallow'",
        f"export UV_PYTHON='{version}'",
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
