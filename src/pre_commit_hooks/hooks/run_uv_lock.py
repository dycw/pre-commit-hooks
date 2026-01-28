from __future__ import annotations

from contextlib import contextmanager, suppress
from functools import partial
from typing import TYPE_CHECKING

from click import command
from tomlkit import parse
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, read_text
from utilities.subprocess import (
    MANAGED_PYTHON,
    PRERELEASE_DISALLOW,
    RESOLUTION_HIGHEST,
    run,
    uv_index_cmd,
    uv_native_tls_cmd,
)

import pre_commit_hooks.hooks.pin_cli_requirements
from pre_commit_hooks.constants import (
    PYPROJECT_TOML,
    certificates_option,
    paths_argument,
    python_uv_index_option,
)
from pre_commit_hooks.utilities import (
    get_array,
    get_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from tomlkit.items import Array
    from utilities.types import MaybeSequenceStr, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_uv_index_option
@certificates_option
def _main(
    *,
    paths: tuple[Path, ...],
    python_uv_index: MaybeSequenceStr | None = None,
    certificates: bool = False,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, index=python_uv_index, native_tls=certificates)
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    index: MaybeSequenceStr | None = None,
    native_tls: bool = False,
) -> bool:
    init = parse(read_text(path))
    with _yield_cli(path=path) as cli:
        if cli is None:
            _run_uv_lock_and_sync(index=index, native_tls=native_tls)
        else:
            cli.clear()
            _ = pre_commit_hooks.hooks.pin_cli_requirements._run(  # noqa: SLF001
                path=path, index=index, native_tls=native_tls
            )
            _run_uv_lock_and_sync(index=index, native_tls=native_tls)
    return parse(read_text(path)) == init


@contextmanager
def _yield_cli(*, path: PathLike = PYPROJECT_TOML) -> Iterator[Array | None]:
    with yield_toml_doc(path) as doc:
        try:
            project = get_table(doc, "project")
        except KeyError:
            yield
            return
        try:
            opt_dependencies = get_table(project, "optional-dependencies")
        except KeyError:
            yield
            return
        with suppress(KeyError):
            yield get_array(opt_dependencies, "cli")


def _run_uv_lock_and_sync(
    *, index: MaybeSequenceStr | None = None, native_tls: bool = False
) -> None:
    run(
        "uv",
        "lock",
        *uv_index_cmd(index=index),
        "--upgrade",
        *RESOLUTION_HIGHEST,
        *PRERELEASE_DISALLOW,
        MANAGED_PYTHON,
        *uv_native_tls_cmd(native_tls=native_tls),
    )
    run(
        "uv",
        "sync",
        "--all-extras",
        "--all-groups",
        *uv_index_cmd(index=index),
        "--upgrade",
        *RESOLUTION_HIGHEST,
        *PRERELEASE_DISALLOW,
        MANAGED_PYTHON,
        *uv_native_tls_cmd(native_tls=native_tls),
    )


if __name__ == "__main__":
    _main()
