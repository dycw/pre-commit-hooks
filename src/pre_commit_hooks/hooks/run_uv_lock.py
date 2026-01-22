from __future__ import annotations

from functools import partial
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
from utilities.subprocess import run

from pre_commit_hooks.constants import PYPROJECT_TOML, paths_argument
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
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PYPROJECT_TOML) -> bool:
    init = read_text(path)
    with TemporaryDirectory() as temp_dir, yield_temp_cwd(temp_dir):
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
            run("uv", "lock", "--upgrade")
            post = 1
            breakpoint()

    return init == post


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
