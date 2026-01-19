from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from tomlkit import table
from utilities.click import CONTEXT_SETTINGS
from utilities.iterables import always_iterable
from utilities.os import is_pytest

from pre_commit_hooks.constants import (
    DEFAULT_PYTHON_VERSION,
    PYPROJECT_TOML,
    README_MD,
    paths_argument,
    python_version_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    ensure_contains_partial_str,
    get_set_aot,
    get_set_array,
    get_set_table,
    get_table,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

    from tomlkit import TOMLDocument
    from tomlkit.items import Table
    from utilities.types import MaybeSequenceStr, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_version_option
def _main(
    *, paths: tuple[Path, ...], python_version: str = DEFAULT_PYTHON_VERSION
) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(
        *(
            partial(_run, path=p.parent / PYPROJECT_TOML, python_version=python_version)
            for p in paths
        )
    )


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    python_version: str = DEFAULT_PYTHON_VERSION,
    description: str | None = None,
    python_package_name_external: str | None = None,
    python_package_name_internal: str | None = None,
    python_uv_index: MaybeSequenceStr | None = None,
    readme: bool = False,
) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        build_system = get_set_table(doc, "build-system")
        build_system["build-backend"] = "uv_build"
        build_system["requires"] = ["uv_build"]
        project = get_set_table(doc, "project")
        project["requires-python"] = f">= {python_version}"
        project.setdefault("version", "0.1.0")
        dependency_groups = get_set_table(doc, "dependency-groups")
        dev = get_set_array(dependency_groups, "dev")
        _ = ensure_contains_partial_str(dev, "dycw-utilities[test]")
        _ = ensure_contains_partial_str(dev, "pyright")
        _ = ensure_contains_partial_str(dev, "rich")
    if description is not None:
        _add_description(description, path=path, modifications=modifications)
    if python_package_name_external is not None:
        _add_external_name(
            python_package_name_external, path=path, modifications=modifications
        )
    if python_package_name_internal is not None:
        _add_internal_name(
            python_package_name_internal, path=path, modifications=modifications
        )
    if python_uv_index is not None:
        for name_and_url in always_iterable(python_uv_index):
            _add_index(name_and_url, path=path, modifications=modifications)
    if readme:
        _add_readme(path=path, modifications=modifications)
    return len(modifications) == 0


def _add_description(
    description: str,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_toml_doc(path, modifications=modifications) as doc:
        project = get_table(doc, "project")
        project["description"] = description


def _add_external_name(
    name: str,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_toml_doc(path, modifications=modifications) as doc:
        project = get_table(doc, "project")
        project["name"] = name


def _add_internal_name(
    name: str,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_toml_doc(path, modifications=modifications) as doc:
        uv = _get_tool_uv(doc)
        build_backend = get_set_table(uv, "build-backend")
        build_backend["module-name"] = name
        build_backend["module-root"] = "src"


def _add_index(
    name_and_url: str,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_toml_doc(path, modifications=modifications) as doc:
        uv = _get_tool_uv(doc)
        indexes = get_set_aot(uv, "index")
        tab = table()
        tab["explicit"] = True
        name, url = name_and_url
        tab["name"] = name
        tab["url"] = url
        ensure_contains(indexes, tab)


def _add_readme(
    *, path: PathLike = PYPROJECT_TOML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_toml_doc(path, modifications=modifications) as doc:
        project = get_table(doc, "project")
        project["readme"] = README_MD


def _get_tool_uv(doc: TOMLDocument, /) -> Table:
    tool = get_set_table(doc, "tool")
    return get_set_table(tool, "uv")


if __name__ == "__main__":
    _main()
