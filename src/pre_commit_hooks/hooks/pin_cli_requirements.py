from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from tomlkit import string
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.packaging import Requirement

from pre_commit_hooks.constants import (
    PYPROJECT_TOML,
    paths_argument,
    python_uv_index_option,
    python_uv_native_tls_option,
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

    from utilities.types import MaybeSequenceStr, PathLike

    from pre_commit_hooks.types import VersionSet


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_uv_index_option
@python_uv_native_tls_option
def _main(
    *,
    paths: tuple[Path, ...],
    python_uv_index: MaybeSequenceStr | None = None,
    python_uv_native_tls: bool = False,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    versions = get_version_set(index=python_uv_index, native_tls=python_uv_native_tls)
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            versions=versions,
            index=python_uv_index,
            native_tls=python_uv_native_tls,
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
    if versions is None:
        versions_use = get_version_set(index=index, native_tls=native_tls)
    else:
        versions_use = versions
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        try:
            project = get_table(doc, "project")
        except KeyError:
            return True
        if "scripts" not in project:
            return True
        dependencies = get_set_array(project, "dependencies")
        opt_dependencies = get_set_table(project, "optional-dependencies")
        cli = get_set_array(opt_dependencies, "cli")
        cli.clear()
        for dep in dependencies:
            req = Requirement(dep)
            try:
                version = versions_use[req.name]
            except KeyError:
                pass
            else:
                req = (
                    req
                    .replace(">=", None)
                    .replace("<", None)
                    .replace("==", str(version))
                )
                cli.append(string(str(req)))
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
