from __future__ import annotations

from functools import partial
from itertools import chain
from typing import TYPE_CHECKING

from click import command, option
from pre_commit.utilities import paths_argument
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest

from pre_commit_hooks.constants import (
    BUILTIN,
    DEFAULT_PYTHON_VERSION,
    DYCW_PRE_COMMIT_HOOKS_URL,
    PRE_COMMIT_CONFIG_YAML,
    PYPROJECT_TOML,
    STD_PRE_COMMIT_HOOKS_URL,
)
from pre_commit_hooks.utilities import add_pre_commit_config_repo, run_all_maybe_raise

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@option("--python", is_flag=True, default=False)
@option("--python-version", type=str, default=DEFAULT_PYTHON_VERSION)
@option("--ruff", is_flag=True, default=False)
def _main(
    *,
    paths: tuple[Path, ...],
    python: bool = False,
    python_version: str = DEFAULT_PYTHON_VERSION,
    ruff: bool = False,
) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = list(
        chain(
            (partial(_add_check_versions_consistent, path=p) for p in paths),
            (partial(_add_run_version_bump, path=p) for p in paths),
            (partial(_add_standard_hooks, path=p) for p in paths),
        )
    )
    if python:
        funcs.extend(partial(_add_add_future_import_annotations, path=p) for p in paths)
        funcs.extend(partial(_add_format_requirements, path=p) for p in paths)
        funcs.extend(partial(_add_replace_sequence_str, path=p) for p in paths)
        funcs.extend(partial(_add_update_requirements, path=p) for p in paths)
    if ruff:
        funcs.extend(
            partial(_add_ruff_hooks, path=p, python_version=python_version)
            for p in paths
        )
    run_all_maybe_raise(*funcs)


def _add_check_versions_consistent(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "check-versions-consistent",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    return len(modifications) == 0


def _add_run_version_bump(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "run-version-bump",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_standard_hooks(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        BUILTIN,
        "check-added-large-files",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "check-case-conflict",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "check-executables-have-shebangs",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN, "check-json", path=path, modifications=modifications, type_="linter"
    )
    add_pre_commit_config_repo(
        BUILTIN, "check-json5", path=path, modifications=modifications, type_="linter"
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "check-merge-conflict",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "check-symlinks",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN, "check-toml", path=path, modifications=modifications, type_="linter"
    )
    add_pre_commit_config_repo(
        BUILTIN, "check-xml", path=path, modifications=modifications, type_="linter"
    )
    add_pre_commit_config_repo(
        BUILTIN, "check-yaml", path=path, modifications=modifications, type_="linter"
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "detect-private-key",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "end-of-file-fixer",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "fix-byte-order-marker",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "mixed-line-ending",
        path=path,
        modifications=modifications,
        args=("add", ["--fix=lf"]),
        type_="formatter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "no-commit-to-branch",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    add_pre_commit_config_repo(
        BUILTIN,
        "trailing-whitespace",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    add_pre_commit_config_repo(
        STD_PRE_COMMIT_HOOKS_URL,
        "check-illegal-windows-names",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    add_pre_commit_config_repo(
        STD_PRE_COMMIT_HOOKS_URL,
        "destroyed-symlinks",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    add_pre_commit_config_repo(
        STD_PRE_COMMIT_HOOKS_URL,
        "pretty-format-json",
        path=path,
        modifications=modifications,
        rev=True,
        args=("add", ["--autofix"]),
        type_="formatter",
    )
    return len(modifications) == 0


def _add_add_future_import_annotations(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML
) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "add-future-import-annotations",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_format_requirements(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "format-requirements",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_replace_sequence_str(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "replace-sequence-str",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_update_requirements(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "update-requirements",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_ruff_hooks(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python_version: str = DEFAULT_PYTHON_VERSION,
) -> bool:
    modifications: set[Path] = set()
    add_pre_commit_config_repo(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "add-ruff-hooks",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", [f"--python-version={python_version}"]),
        type_="formatter",
    )
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
