from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from tomlkit import table
from utilities.click import CONTEXT_SETTINGS
from utilities.core import (
    TemporaryDirectory,
    copy,
    kebab_case,
    read_text,
    snake_case,
    yield_temp_cwd,
)
from utilities.os import is_pytest
from utilities.subprocess import (
    MANAGED_PYTHON,
    PRERELEASE_DISALLOW,
    RESOLUTION_HIGHEST,
    run,
    uv_index_cmd,
    uv_native_tls_cmd,
)

from pre_commit_hooks.constants import (
    PYPROJECT_TOML,
    PYTHON_VERSION,
    README_MD,
    UV_LOCK,
    certificates_option,
    description_option,
    paths_argument,
    python_package_name_external_option,
    python_package_name_internal_option,
    python_uv_index_option,
    python_version_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_table,
    get_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
    yield_tool_uv,
    yield_tool_uv_index,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet

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
    path = Path(path)
    uv_lock = path.parent / UV_LOCK
    init = read_text(uv_lock)
    with TemporaryDirectory() as temp_dir:
        temp_file = temp_dir / PYPROJECT_TOML
        copy(path, temp_file)
        with yield_toml_doc(temp_file) as doc:
            try:
                project = get_table(doc, "project")
            except KeyError:
                return True
            try:
                opt_dependencies = get_table(project, "optional-dependencies")
            except KeyError:
                return True
            try:
                del opt_dependencies["cli"]
            except KeyError:
                return True
            run(
                "uv",
                "lock",
                *uv_index_cmd(index=index),
                "--upgrade",
                *RESOLUTION_HIGHEST,
                *PRERELEASE_DISALLOW,
                MANAGED_PYTHON,
                *uv_native_tls_cmd(native_tls=native_tls),
                cwd=temp_dir,
            )
            copy(temp_dir / UV_LOCK, uv_lock, overwrite=True)
    return read_text(uv_lock) != init


if __name__ == "__main__":
    _main()
