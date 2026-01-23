from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from tomlkit import table
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, snake_case, substitute
from utilities.version import Version3

from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    PYPROJECT_TOML,
    paths_argument,
    python_package_name_internal_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_aot,
    get_set_table,
    get_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
    yield_tool,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_package_name_internal_option
def _main(
    *, paths: tuple[Path, ...], python_package_name_internal: str | None = None
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=BUMPVERSION_TOML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, package_name=python_package_name_internal)
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = BUMPVERSION_TOML, package_name: str | None = None) -> bool:
    path = Path(path)
    modifications: set[Path] = set()
    with yield_tool(path, modifications=modifications) as table:
        bumpversion = get_set_table(table, "bumpversion")
        bumpversion["allow_dirty"] = True
        bumpversion.setdefault("current_version", str(Version3(0, 1, 0)))
    if package_name is not None:
        _add_python(package_name, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_python(
    package_name: str,
    /,
    *,
    path: PathLike = BUMPVERSION_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    path = Path(path)
    _add_file(
        path.parent / PYPROJECT_TOML,
        'version = "${version}"',
        path_bumpversion=path,
        modifications=modifications,
    )
    _add_file(
        path.parent / "src" / snake_case(package_name) / "__init__.py",
        '__version__ = "${version}"',
        path_bumpversion=path,
        modifications=modifications,
    )


def _add_file(
    path_data: PathLike,
    template: PathLike,
    /,
    *,
    path_bumpversion: PathLike = BUMPVERSION_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_toml_doc(path_bumpversion, modifications=modifications) as doc:
        tool = get_table(doc, "tool")
        bumpversion = get_table(tool, "bumpversion")
        files = get_set_aot(bumpversion, "files")
        tab = table()
        tab["filename"] = str(path_data)
        tab["search"] = substitute(template, version="{current_version}")
        tab["replace"] = substitute(template, version="{new_version}")
        ensure_contains(files, tab)


if __name__ == "__main__":
    _main()
