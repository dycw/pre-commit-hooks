from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from tomlkit import table
from utilities.click import CONTEXT_SETTINGS
from utilities.core import always_iterable, is_pytest, kebab_case, snake_case

from pre_commit_hooks.constants import (
    PYPROJECT_TOML,
    PYTHON_VERSION,
    README_MD,
    description_option,
    paths_argument,
    python_package_name_external_option,
    python_package_name_internal_option,
    python_uv_index_option,
    python_version_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    ensure_contains_partial_str,
    get_set_array,
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
@python_version_option
@description_option
@python_uv_index_option
@python_package_name_external_option
@python_package_name_internal_option
def _main(
    *,
    paths: tuple[Path, ...],
    python_version: str | None = None,
    description: str | None = None,
    python_uv_index: MaybeSequenceStr | None = None,
    python_package_name_external: str | None = None,
    python_package_name_internal: str | None = None,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            version=python_version,
            description=description,
            index=python_uv_index,
            name_external=python_package_name_external,
            name_internal=python_package_name_internal,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    version: str | None = None,
    description: str | None = None,
    index: MaybeSequenceStr | None = None,
    name_external: str | None = None,
    name_internal: str | None = None,
) -> bool:
    path = Path(path)
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        build_system = get_set_table(doc, "build-system")
        build_system["build-backend"] = "uv_build"
        build_system["requires"] = ["uv_build"]
        project = get_set_table(doc, "project")
        project["readme"] = str(path.parent / README_MD)
        version_use = PYTHON_VERSION if version is None else version
        project["requires-python"] = f">= {version_use}"
        project.setdefault("version", "0.1.0")
        dependency_groups = get_set_table(doc, "dependency-groups")
        dev = get_set_array(dependency_groups, "dev")
        _ = ensure_contains_partial_str(dev, "dycw-utilities[test]")
        _ = ensure_contains_partial_str(dev, "pyright")
    if description is not None:
        _add_description(description, path=path, modifications=modifications)
    if index is not None:
        for index_i in always_iterable(index):
            _add_index(index_i, path=path, modifications=modifications)
    if name_external is not None:
        _add_external_name(name_external, path=path, modifications=modifications)
    if name_internal is not None:
        _add_internal_name(name_internal, path=path, modifications=modifications)
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
        project["name"] = kebab_case(name)


def _add_internal_name(
    name: str,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_tool_uv(path, modifications=modifications) as table:
        build_backend = get_set_table(table, "build-backend")
        build_backend["module-name"] = snake_case(name)
        build_backend["module-root"] = "src"


def _add_index(
    name_and_url: str,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_tool_uv_index(path, modifications=modifications) as index:
        tab = table()
        tab["explicit"] = True
        name, url = name_and_url.split("=")
        tab["name"] = name
        tab["url"] = url
        ensure_contains(index, tab)


if __name__ == "__main__":
    _main()
