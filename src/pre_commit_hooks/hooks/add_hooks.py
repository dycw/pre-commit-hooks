from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Literal, assert_never

from click import command, option
from utilities.click import CONTEXT_SETTINGS
from utilities.concurrent import concurrent_map
from utilities.os import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    BUILTIN,
    DEFAULT_PYTHON_VERSION,
    DOCKERFMT_URL,
    DYCW_PRE_COMMIT_HOOKS_URL,
    FORMATTER_PRIORITY,
    LINTER_PRIORITY,
    PRE_COMMIT_CONFIG_YAML,
    PYPROJECT_TOML,
    RUFF_URL,
    SHELLCHECK_URL,
    SHFMT_URL,
    STD_PRE_COMMIT_HOOKS_URL,
    TAPLO_URL,
    UV_URL,
    paths_argument,
    python_package_name_option,
    python_version_option,
)
from pre_commit_hooks.utilities import (
    apply,
    ensure_contains,
    ensure_contains_partial_dict,
    get_set_list_dicts,
    get_set_list_strs,
    run_all_maybe_raise,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import IntOrAll, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@option("--ci", is_flag=True, default=False)
@option("--docker", is_flag=True, default=False)
@option("--python", is_flag=True, default=False)
@python_package_name_option
@python_version_option
@option("--shell", is_flag=True, default=False)
@option("--toml", is_flag=True, default=False)
@option("--max-workers", type=int, default=None)
def _main(
    *,
    paths: tuple[Path, ...],
    ci: bool = False,
    docker: bool = False,
    python: bool = False,
    python_package_name: str | None = None,
    python_version: str = DEFAULT_PYTHON_VERSION,
    shell: bool = False,
    toml: bool = False,
    max_workers: int | None = None,
) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(
        *(
            partial(
                _run,
                path=p,
                ci=ci,
                docker=docker,
                python=python,
                python_package_name=python_package_name,
                python_version=python_version,
                shell=shell,
                toml=toml,
                max_workers="all" if max_workers is None else max_workers,
            )
            for p in paths
        )
    )


def _run(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    ci: bool = False,
    docker: bool = False,
    python: bool = False,
    python_package_name: str | None = None,
    python_version: str = DEFAULT_PYTHON_VERSION,
    shell: bool = False,
    toml: bool = False,
    max_workers: IntOrAll = "all",
) -> bool:
    funcs: list[Callable[[], bool]] = [
        partial(_add_check_versions_consistent, path=path),
        partial(_add_format_pre_commit_config, path=path),
        partial(_add_run_prek_autoupdate, path=path),
        partial(_add_run_version_bump, path=path),
        partial(_add_setup_bump_my_version, path=path),
        partial(_add_standard_hooks, path=path),
    ]
    if ci:
        funcs.append(partial(_add_update_ci_extensions, path=path))
    if docker:
        funcs.append(partial(_add_dockerfmt, path=path))
    if python:
        funcs.append(partial(_add_add_future_import_annotations, path=path))
        funcs.append(partial(_add_format_requirements, path=path))
        funcs.append(partial(_add_replace_sequence_str, path=path))
        funcs.append(partial(_add_ruff_check, path=path))
        funcs.append(partial(_add_ruff_format, path=path))
        funcs.append(
            partial(
                _add_setup_bump_my_version,
                path=path,
                python_package_name=python_package_name,
            )
        )
        funcs.append(partial(_add_setup_git, path=path))
        funcs.append(
            partial(_add_setup_pyright, path=path, python_version=python_version)
        )
        funcs.append(partial(_add_setup_ruff, path=path, python_version=python_version))
        funcs.append(partial(_add_update_requirements, path=path))
        funcs.append(partial(_add_uv_lock, path=path))
    if shell:
        funcs.append(partial(_add_shellcheck, path=path))
        funcs.append(partial(_add_shfmt, path=path))
    if toml:
        funcs.append(partial(_add_taplo_format, path=path))
    return all(
        concurrent_map(apply, funcs, parallelism="threads", max_workers=max_workers)
    )


def _add_check_versions_consistent(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "check-versions-consistent",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    return len(modifications) == 0


def _add_format_pre_commit_config(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "format-pre-commit-config",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    return len(modifications) == 0


def _add_run_prek_autoupdate(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "run-prek-autoupdate",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_run_version_bump(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "run-version-bump",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_setup_bump_my_version(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, python_package_name: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_package_name is not None:
        args.append(f"--python-package-name={python_package_name}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-bump-my-version",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", args) if len(args) >= 1 else None,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_standard_hooks(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        BUILTIN,
        "check-added-large-files",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN,
        "check-case-conflict",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN,
        "check-executables-have-shebangs",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN, "check-json", path=path, modifications=modifications, type_="linter"
    )
    _add_hook(
        BUILTIN, "check-json5", path=path, modifications=modifications, type_="linter"
    )
    _add_hook(
        BUILTIN,
        "check-merge-conflict",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN,
        "check-symlinks",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN, "check-toml", path=path, modifications=modifications, type_="linter"
    )
    _add_hook(
        BUILTIN, "check-xml", path=path, modifications=modifications, type_="linter"
    )
    _add_hook(
        BUILTIN, "check-yaml", path=path, modifications=modifications, type_="linter"
    )
    _add_hook(
        BUILTIN,
        "detect-private-key",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN,
        "end-of-file-fixer",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    _add_hook(
        BUILTIN,
        "fix-byte-order-marker",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    _add_hook(
        BUILTIN,
        "mixed-line-ending",
        path=path,
        modifications=modifications,
        args=("exact", ["--fix=lf"]),
        type_="formatter",
    )
    _add_hook(
        BUILTIN,
        "no-commit-to-branch",
        path=path,
        modifications=modifications,
        type_="linter",
    )
    _add_hook(
        BUILTIN,
        "trailing-whitespace",
        path=path,
        modifications=modifications,
        type_="formatter",
    )
    _add_hook(
        STD_PRE_COMMIT_HOOKS_URL,
        "check-illegal-windows-names",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    _add_hook(
        STD_PRE_COMMIT_HOOKS_URL,
        "destroyed-symlinks",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    _add_hook(
        STD_PRE_COMMIT_HOOKS_URL,
        "pretty-format-json",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", ["--autofix"]),
        type_="formatter",
    )
    return len(modifications) == 0


def _add_update_ci_extensions(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "update-ci-extensions",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_dockerfmt(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DOCKERFMT_URL,
        "dockerfmt",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", ["--newline", "--write"]),
        type_="formatter",
    )
    return len(modifications) == 0


def _add_add_future_import_annotations(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML
) -> bool:
    modifications: set[Path] = set()
    _add_hook(
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
    _add_hook(
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
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "replace-sequence-str",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_ruff_check(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        RUFF_URL,
        "ruff-check",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", ["--fix"]),
        type_="linter",
    )
    return len(modifications) == 0


def _add_ruff_format(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        RUFF_URL,
        "ruff-format",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_setup_git(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-git",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_setup_pyright(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python_version: str = DEFAULT_PYTHON_VERSION,
) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pyright",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", [f"--python-version={python_version}"]),
        type_="formatter",
    )
    return len(modifications) == 0


def _add_setup_ruff(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python_version: str = DEFAULT_PYTHON_VERSION,
) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ruff",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", [f"--python-version={python_version}"]),
        type_="formatter",
    )
    return len(modifications) == 0


def _add_update_requirements(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "update-requirements",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_uv_lock(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    args: list[str] = [
        "--upgrade",
        "--resolution",
        "highest",
        "--prerelease",
        "disallow",
    ]
    _add_hook(
        UV_URL,
        "uv-lock",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", args),
        type_="formatter",
    )
    return len(modifications) == 0


def _add_shellcheck(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        SHELLCHECK_URL,
        "shellcheck",
        path=path,
        modifications=modifications,
        rev=True,
        type_="linter",
    )
    return len(modifications) == 0


def _add_shfmt(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        SHFMT_URL,
        "shfmt",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_taplo_format(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    args: list[str] = [
        "--option",
        "indent_tables=true",
        "--option",
        "indent_entries=true",
        "--option",
        "reorder_keys=true",
    ]
    _add_hook(
        TAPLO_URL,
        "taplo-format",
        path=path,
        modifications=modifications,
        rev=True,
        args=("exact", args),
        type_="linter",
    )
    return len(modifications) == 0


##


def _add_hook(
    url: str,
    id_: str,
    /,
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
    rev: bool = False,
    name: str | None = None,
    entry: str | None = None,
    language: str | None = None,
    files: str | None = None,
    types_or: list[str] | None = None,
    args: tuple[Literal["add", "exact"], list[str]] | None = None,
    type_: Literal["formatter", "linter"] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos_list = get_set_list_dicts(dict_, "repos")
        repo_dict = ensure_contains_partial_dict(
            repos_list, {"repo": url}, extra={"rev": "master"} if rev else {}
        )
        hooks_list = get_set_list_dicts(repo_dict, "hooks")
        hook_dict = ensure_contains_partial_dict(hooks_list, {"id": id_})
        if name is not None:
            hook_dict["name"] = name
        if entry is not None:
            hook_dict["entry"] = entry
        if language is not None:
            hook_dict["language"] = language
        if files is not None:
            hook_dict["files"] = files
        if types_or is not None:
            hook_dict["types_or"] = types_or
        if args is not None:
            match args:
                case "add", list() as args_i:
                    hook_args = get_set_list_strs(hook_dict, "args")
                    ensure_contains(hook_args, *args_i)
                case "exact", list() as args_i:
                    hook_dict["args"] = args_i
                case never:
                    assert_never(never)
        match type_:
            case "formatter":
                hook_dict["priority"] = FORMATTER_PRIORITY
            case "linter":
                hook_dict["priority"] = LINTER_PRIORITY
            case None:
                ...
            case never:
                assert_never(never)


if __name__ == "__main__":
    _main()
