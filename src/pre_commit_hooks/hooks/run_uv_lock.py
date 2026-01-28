from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from tomlkit import array, string
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.packaging import Requirement
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
    certificates_option,
    paths_argument,
    python_uv_index_option,
)
from pre_commit_hooks.utilities import (
    get_set_array,
    get_set_table,
    get_table,
    get_version_set,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from tomlkit.items import Array, Table
    from utilities.types import MaybeSequenceStr, PathLike

    from pre_commit_hooks.types import VersionSet


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
    versions = get_version_set(index=python_uv_index, native_tls=certificates)
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            versions=versions,
            index=python_uv_index,
            native_tls=certificates,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    versions: VersionSet | None = None,
    index: MaybeSequenceStr | None = None,
    native_tls: bool = False,
) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        try:
            project = get_table(doc, "project")
        except KeyError:
            pass
        else:
            if "scripts" in project:
                _pin_dependencies(
                    project, versions=versions, index=index, native_tls=native_tls
                )
        _run_uv_lock_and_sync(index=index, native_tls=native_tls)
    return len(modifications) == 0


def _pin_dependencies(
    project: Table,
    /,
    *,
    versions: VersionSet | None = None,
    index: MaybeSequenceStr | None = None,
    native_tls: bool = False,
) -> None:
    dependencies = get_set_array(project, "dependencies")
    opt_dependencies = get_set_table(project, "optional-dependencies")
    cli = get_set_array(opt_dependencies, "cli")
    pinned = _get_pinned(
        dependencies, versions=versions, index=index, native_tls=native_tls
    )
    cli.clear()
    _run_uv_lock_and_sync(index=index, native_tls=native_tls)
    cli.extend(pinned)


def _get_pinned(
    dependencies: Array,
    /,
    *,
    versions: VersionSet | None = None,
    index: MaybeSequenceStr | None = None,
    native_tls: bool = False,
) -> Array:
    if versions is None:
        versions_use = get_version_set(index=index, native_tls=native_tls)
    else:
        versions_use = versions
    result = array()
    for dep in dependencies:
        req = Requirement(dep)
        try:
            version = versions_use[req.name]
        except KeyError:
            pass
        else:
            pinned = (
                req.replace(">=", None).replace("<", None).replace("==", str(version))
            )
            result.append(string(str(pinned)))
    return result


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
