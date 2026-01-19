from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from tomlkit import table
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.string import substitute
from utilities.version import Version3

from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    PYPROJECT_TOML,
    paths_argument,
    python_package_name_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_aot,
    get_set_table,
    get_table,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import MutableSet

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_package_name_option
def _main(*, paths: tuple[Path, ...], python_package_name: str | None = None) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(
        *(
            partial(
                _run,
                path=p.parent / BUMPVERSION_TOML,
                python_package_name=python_package_name,
            )
            for p in paths
        )
    )


def _run(
    *, path: PathLike = BUMPVERSION_TOML, python_package_name: str | None = None
) -> bool:
    path = Path(path)
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        tool = get_set_table(doc, "tool")
        bumpversion = get_set_table(tool, "bumpversion")
        bumpversion["allow_dirty"] = True
        bumpversion.setdefault("current_version", str(Version3(0, 1, 0)))
    if python_package_name is not None:
        _add_file(
            'version = "${version}"',
            path.parent / PYPROJECT_TOML,
            path_bumpversion_toml=path,
            modifications=modifications,
        )
        _add_file(
            '__version__ = "${version}"',
            path.parent / "src" / python_package_name / "__init__.py",
            path_bumpversion_toml=path,
            modifications=modifications,
        )
    return len(modifications) == 0


def _add_file(
    filename: PathLike,
    path_data: PathLike,
    /,
    *,
    path_bumpversion_toml: PathLike = BUMPVERSION_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_toml_doc(path_bumpversion_toml, modifications=modifications) as doc:
        tool = get_table(doc, "tool")
        bumpversion = get_table(tool, "bumpversion")
        files = get_set_aot(bumpversion, "files")
        tab = table()
        tab["filename"] = str(filename)
        tab["search"] = substitute(path_data, version="{current_version}")
        tab["replace"] = substitute(path_data, version="{new_version}")
        ensure_contains(files, tab)


if __name__ == "__main__":
    _main()
