from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command, option
from tomlkit import string
from utilities.click import CONTEXT_SETTINGS, ListStrs
from utilities.os import is_pytest
from utilities.packaging import Requirement

from pre_commit_hooks.constants import PYPROJECT_TOML, paths_argument
from pre_commit_hooks.utilities import (
    get_set_array,
    get_set_table,
    get_table,
    get_version_set,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike

    from pre_commit_hooks.types import VersionSet


@command(**CONTEXT_SETTINGS)
@paths_argument
@option("--index", type=ListStrs(), default=None)
@option("--native-tls", is_flag=True, default=False)
def _main(
    *, paths: tuple[Path, ...], index: list[str] | None = None, native_tls: bool = False
) -> None:
    if is_pytest():
        return
    versions = get_version_set(index=index, native_tls=native_tls)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, versions=versions, index=index, native_tls=native_tls)
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    versions: VersionSet | None = None,
    index: list[str] | None = None,
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
