from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Literal, assert_never

from click import command, option
from utilities.click import CONTEXT_SETTINGS
from utilities.core import always_iterable, is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    BUILTIN,
    DOCKERFMT_URL,
    DYCW_PRE_COMMIT_HOOKS_URL,
    EDITOR_PRIORITY,
    FORMATTER_PRIORITY,
    LINTER_PRIORITY,
    LOCAL,
    PRE_COMMIT_CONFIG_YAML,
    PRE_COMMIT_PRIORITY,
    PYPROJECT_TOML,
    RUFF_URL,
    SHELLCHECK_URL,
    SHFMT_URL,
    STD_PRE_COMMIT_HOOKS_URL,
    STYLUA_URL,
    TAPLO_URL,
    XMLFORMATTER_URL,
    certificates_option,
    ci_pytest_os_option,
    ci_pytest_python_version_option,
    ci_pytest_runs_on_option,
    ci_tag_all_option,
    description_option,
    paths_argument,
    python_option,
    python_package_name_external_option,
    python_package_name_internal_option,
    python_uv_index_option,
    python_version_option,
    repo_name_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    ensure_contains_partial_dict,
    get_set_list_dicts,
    get_set_list_strs,
    re_insert_hook_dict,
    run_all,
    run_all_maybe_raise,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@certificates_option
@option("--ci-github", is_flag=True, default=False)
@option("--ci-gitea", is_flag=True, default=False)
@ci_pytest_os_option
@ci_pytest_python_version_option
@ci_pytest_runs_on_option
@ci_tag_all_option
@description_option
@option("--direnv", is_flag=True, default=False)
@option("--docker", is_flag=True, default=False)
@option("--fish", is_flag=True, default=False)
@option("--just", is_flag=True, default=False)
@option("--lua", is_flag=True, default=False)
@option("--prettier", is_flag=True, default=False)
@python_option
@python_package_name_external_option
@python_package_name_internal_option
@python_uv_index_option
@python_version_option
@repo_name_option
@option("--shell", is_flag=True, default=False)
@option("--toml", is_flag=True, default=False)
@option("--xml", is_flag=True, default=False)
def _main(
    *,
    paths: tuple[Path, ...],
    certificates: bool = False,
    ci_github: bool = False,
    ci_gitea: bool = False,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_python_version: MaybeSequenceStr | None = None,
    ci_pytest_runs_on: MaybeSequenceStr | None = None,
    ci_tag_all: bool = False,
    description: str | None = None,
    direnv: bool = False,
    docker: bool = False,
    fish: bool = False,
    just: bool = False,
    lua: bool = False,
    prettier: bool = False,
    python: bool = False,
    python_package_name_external: str | None = None,
    python_package_name_internal: str | None = None,
    python_uv_index: MaybeSequenceStr | None = None,
    python_version: str | None = None,
    repo_name: str | None = None,
    shell: bool = False,
    toml: bool = False,
    xml: bool = False,
) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            certificates=certificates,
            ci_github=ci_github,
            ci_gitea=ci_gitea,
            ci_pytest_os=ci_pytest_os,
            ci_pytest_python_version=ci_pytest_python_version,
            ci_pytest_runs_on=ci_pytest_runs_on,
            ci_tag_all=ci_tag_all,
            description=description,
            direnv=direnv,
            docker=docker,
            fish=fish,
            just=just,
            lua=lua,
            prettier=prettier,
            python=python,
            python_package_name_external=python_package_name_external,
            python_package_name_internal=python_package_name_internal,
            python_uv_index=python_uv_index,
            python_version=python_version,
            repo_name=repo_name,
            shell=shell,
            toml=toml,
            xml=xml,
        )
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    certificates: bool = False,
    ci_github: bool = False,
    ci_gitea: bool = False,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_python_version: MaybeSequenceStr | None = None,
    ci_pytest_runs_on: MaybeSequenceStr | None = None,
    ci_tag_all: bool = False,
    description: str | None = None,
    direnv: bool = False,
    docker: bool = False,
    fish: bool = False,
    just: bool = False,
    lua: bool = False,
    prettier: bool = False,
    python: bool = False,
    python_package_name_external: str | None = None,
    python_package_name_internal: str | None = None,
    python_uv_index: MaybeSequenceStr | None = None,
    python_version: str | None = None,
    repo_name: str | None = None,
    shell: bool = False,
    toml: bool = False,
    xml: bool = False,
) -> bool:
    funcs: list[Callable[[], bool]] = [
        partial(_add_check_versions_consistent, path=path),
        partial(_add_format_pre_commit_config, path=path),
        partial(_add_run_prek_autoupdate, path=path),
        partial(_add_run_version_bump, path=path),
        partial(_add_setup_bump_my_version, path=path),
        partial(_add_setup_git, path=path, python=python),
        partial(_add_setup_pre_commit, path=path),
        partial(
            _add_setup_readme, path=path, repo_name=repo_name, description=description
        ),
        partial(_add_standard_hooks, path=path),
    ]
    if ci_github or ci_gitea:
        funcs.append(partial(_add_update_ci_action_versions, path=path))
        funcs.append(partial(_add_update_ci_extensions, path=path))
    if ci_github:
        funcs.append(
            partial(
                _add_setup_ci_push,
                path=path,
                certificates=certificates,
                ci_tag_all=ci_tag_all,
                python=python,
            )
        )
    if ci_github and python:
        funcs.append(
            partial(
                _add_setup_ci_pull_request,
                path=path,
                repo_name=repo_name,
                certificates=certificates,
                python_version=python_version,
                ci_pytest_runs_on=ci_pytest_runs_on,
                ci_pytest_os=ci_pytest_os,
                ci_pytest_python_version=ci_pytest_python_version,
            )
        )
    if ci_gitea:
        funcs.append(
            partial(
                _add_setup_ci_push,
                path=path,
                gitea=True,
                certificates=certificates,
                ci_tag_all=ci_tag_all,
                python=python,
            )
        )
    if ci_gitea and python:
        funcs.append(
            partial(
                _add_setup_ci_pull_request,
                path=path,
                gitea=True,
                repo_name=repo_name,
                certificates=certificates,
                python_version=python_version,
                ci_pytest_runs_on=ci_pytest_runs_on,
                ci_pytest_os=ci_pytest_os,
                ci_pytest_python_version=ci_pytest_python_version,
            )
        )
    if direnv and not python:
        funcs.append(
            partial(_add_setup_direnv, path=path, python_version=python_version)
        )
    if docker:
        funcs.append(partial(_add_dockerfmt, path=path))
    if fish:
        funcs.append(partial(_add_fish_indent, path=path))
    if just:
        funcs.append(partial(_add_setup_just, path=path))
    if lua:
        funcs.append(partial(_add_stylua, path=path))
    if prettier:
        funcs.append(partial(_add_prettier, path=path))
    if python:
        funcs.append(partial(_add_add_future_import_annotations, path=path))
        funcs.append(partial(_add_format_requirements, path=path))
        funcs.append(partial(_add_replace_sequence_str, path=path))
        funcs.append(partial(_add_ruff_check, path=path))
        funcs.append(partial(_add_ruff_format, path=path))
        funcs.append(
            partial(
                _add_run_uv_lock,
                path=path,
                python_uv_index=python_uv_index,
                certificates=certificates,
            )
        )
        funcs.append(
            partial(
                _add_setup_bump_my_version,
                path=path,
                python_package_name_internal=python_package_name_internal,
            )
        )
        funcs.append(partial(_add_setup_coverage, path=path))
        funcs.append(
            partial(
                _add_setup_direnv,
                path=path,
                python=True,
                certificates=certificates,
                python_version=python_version,
            )
        )
        funcs.append(
            partial(
                _add_setup_pyproject,
                path=path,
                python_version=python_version,
                description=description,
                python_uv_index=python_uv_index,
                python_package_name_external=python_package_name_external,
                python_package_name_internal=python_package_name_internal,
            )
        )
        funcs.append(
            partial(_add_setup_pyright, path=path, python_version=python_version)
        )
        funcs.append(
            partial(
                _add_setup_pytest,
                path=path,
                python_package_name_internal=python_package_name_internal,
            )
        )
        funcs.append(partial(_add_setup_ruff, path=path, python_version=python_version))
        funcs.append(
            partial(
                _add_update_requirements,
                path=path,
                python_uv_index=python_uv_index,
                certificates=certificates,
            )
        )
    if shell:
        funcs.append(partial(_add_shellcheck, path=path))
        funcs.append(partial(_add_shfmt, path=path))
    if toml:
        funcs.append(partial(_add_taplo_format, path=path))
    if xml:
        funcs.append(partial(_add_xmlformatter, path=path))
    return run_all(*funcs)


##


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
        type_="editor",
    )
    return len(modifications) == 0


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


def _add_dockerfmt(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DOCKERFMT_URL,
        "dockerfmt",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=["--newline", "--write"],
        type_="formatter",
    )
    return len(modifications) == 0


def _add_fish_indent(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        LOCAL,
        "fish_indent",
        path=path,
        modifications=modifications,
        name="fish_indent",
        entry="fish_indent",
        language="unsupported",
        files=r"\.fish$",
        args_exact=["--write"],
        type_="formatter",
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


def _add_prettier(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        LOCAL,
        "prettier",
        path=path,
        modifications=modifications,
        name="prettier",
        entry="npx prettier --write",
        language="unsupported",
        types_or=["markdown", "yaml"],
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
        type_="editor",
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
        type_="pre-commit",
    )
    return len(modifications) == 0


def _add_run_uv_lock(
    *,
    path: PathLike = PYPROJECT_TOML,
    python_uv_index: MaybeSequenceStr | None = None,
    certificates: bool = False,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_uv_index is not None:
        args.append(f"--python-uv-index={','.join(always_iterable(python_uv_index))}")
    if certificates:
        args.append("--certificates")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "run-uv-lock",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
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
        args_exact=["--fix"],
        type_="editor",
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


def _add_run_version_bump(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "run-version-bump",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_bump_my_version(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python_package_name_internal: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_package_name_internal is not None:
        args.append(f"--python-package-name-internal={python_package_name_internal}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-bump-my-version",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_ci_pull_request(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    gitea: bool = False,
    repo_name: str | None = None,
    certificates: bool = False,
    python_version: str | None = None,
    ci_pytest_runs_on: MaybeSequenceStr | None = None,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_python_version: MaybeSequenceStr | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if gitea:
        args.append("--gitea")
    if repo_name is not None:
        args.append(f"--repo-name={repo_name}")
    if certificates:
        args.append("--certificates")
    if python_version is not None:
        args.append(f"--python-version={python_version}")
    if ci_pytest_runs_on is not None:
        args.append(
            f"--ci-pytest-runs-on={','.join(always_iterable(ci_pytest_runs_on))}"
        )
    if ci_pytest_os is not None:
        args.append(f"--ci-pytest-os={','.join(always_iterable(ci_pytest_os))}")
    if ci_pytest_python_version is not None:
        args.append(
            f"--ci-pytest-python-version={','.join(always_iterable(ci_pytest_python_version))}"
        )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ci-pull-request",
        path=path,
        modifications=modifications,
        args_exact=args if len(args) >= 1 else None,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_ci_push(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    gitea: bool = False,
    certificates: bool = False,
    ci_tag_all: bool = False,
    python: bool = False,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if gitea:
        args.append("--gitea")
    if certificates:
        args.append("--certificates")
    if ci_tag_all:
        args.append("--ci-tag-all")
    if python:
        args.append("--python")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ci-push",
        path=path,
        modifications=modifications,
        args_exact=args if len(args) >= 1 else None,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_coverage(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-coverage",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_direnv(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python: bool = False,
    certificates: bool = False,
    python_version: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python:
        args.append("--python")
    if certificates:
        args.append("--certificates")
    if python_version is not None:
        args.append(f"--python-version={python_version}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-direnv",
        path=path,
        modifications=modifications,
        rev=True,
        args_add=args if len(args) >= 1 else None,
        args_add_sort=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_git(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, python: bool = False
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python:
        args.append("--python")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-git",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_just(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-just",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_pre_commit(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pre-commit",
        path=path,
        modifications=modifications,
        rev=True,
        type_="pre-commit",
    )
    return len(modifications) == 0


def _add_setup_pyproject(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python_version: str | None = None,
    description: str | None = None,
    python_uv_index: MaybeSequenceStr | None = None,
    python_package_name_external: str | None = None,
    python_package_name_internal: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_version is not None:
        args.append(f"--python-version={python_version}")
    if description is not None:
        args.append(f"--description={description}")
    if python_uv_index is not None:
        args.append(f"--python-uv-index={','.join(always_iterable(python_uv_index))}")
    if python_package_name_external is not None:
        args.append(f"--python-package-name-external={python_package_name_external}")
    if python_package_name_internal is not None:
        args.append(f"--python-package-name-internal={python_package_name_internal}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pyproject",
        path=path,
        modifications=modifications,
        rev=True,
        args_add=args if len(args) >= 1 else None,
        args_add_sort=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_pyright(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, python_version: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_version is not None:
        args.append(f"--python-version={python_version}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pyright",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_pytest(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    python_package_name_internal: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_package_name_internal is not None:
        args.append(f"--python-package-name-internal={python_package_name_internal}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pytest",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_readme(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    repo_name: str | None = None,
    description: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if repo_name is not None:
        args.append(f"--repo-name={repo_name}")
    if description is not None:
        args.append(f"--description={description}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-readme",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_ruff(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, python_version: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_version is not None:
        args.append(f"--python-version={python_version}")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ruff",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
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
        type_="editor",
    )
    _add_hook(
        BUILTIN,
        "fix-byte-order-marker",
        path=path,
        modifications=modifications,
        type_="editor",
    )
    _add_hook(
        BUILTIN,
        "mixed-line-ending",
        path=path,
        modifications=modifications,
        args_exact=["--fix=lf"],
        type_="editor",
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
        type_="editor",
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
        args_exact=["--autofix"],
        type_="editor",
    )
    return len(modifications) == 0


def _add_stylua(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        STYLUA_URL,
        "stylua",
        path=path,
        modifications=modifications,
        rev=True,
        type_="formatter",
    )
    return len(modifications) == 0


def _add_taplo_format(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        TAPLO_URL,
        "taplo-format",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=[
            "--option",
            "indent_tables=true",
            "--option",
            "indent_entries=true",
            "--option",
            "reorder_keys=true",
        ],
        type_="linter",
    )
    return len(modifications) == 0


def _add_update_ci_action_versions(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "update-ci-action-versions",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
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
        type_="editor",
    )
    return len(modifications) == 0


def _add_update_requirements(
    *,
    path: PathLike = PYPROJECT_TOML,
    python_uv_index: MaybeSequenceStr | None = None,
    certificates: bool = False,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if python_uv_index is not None:
        args.append(f"--python-uv-index={','.join(always_iterable(python_uv_index))}")
    if certificates:
        args.append("--certificates")
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "update-requirements",
        path=path,
        modifications=modifications,
        rev=True,
        args_add=args if len(args) >= 1 else None,
        args_add_sort=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_xmlformatter(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        XMLFORMATTER_URL,
        "xml-formatter",
        path=path,
        modifications=modifications,
        rev=True,
        types=[],
        types_or=["plist", "xml"],
        args_exact=["--eof-newline"],
        type_="formatter",
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
    types: list[str] | None = None,
    types_or: list[str] | None = None,
    args_add: list[str] | None = None,
    args_add_sort: bool = False,
    args_exact: list[str] | None = None,
    type_: Literal["pre-commit", "editor", "formatter", "linter"] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos = get_set_list_dicts(dict_, "repos")
        repo = ensure_contains_partial_dict(repos, {"repo": url})
        if rev:
            repo.setdefault("rev", "master")
        hooks = get_set_list_dicts(repo, "hooks")
        hook = ensure_contains_partial_dict(hooks, {"id": id_})
        if name is not None:
            hook["name"] = name
        if entry is not None:
            hook["entry"] = entry
        if language is not None:
            hook["language"] = language
        if files is not None:
            hook["files"] = files
        if types is not None:
            hook["types"] = types
        if types_or is not None:
            hook["types_or"] = types_or
        if args_add is not None:
            args = get_set_list_strs(hook, "args")
            ensure_contains(args, *args_add)
            if args_add_sort:
                args.sort()
        if args_exact is not None:
            hook["args"] = args_exact
        match type_:
            case "pre-commit":
                hook["priority"] = PRE_COMMIT_PRIORITY
            case "editor":
                hook["priority"] = EDITOR_PRIORITY
            case "formatter":
                hook["priority"] = FORMATTER_PRIORITY
            case "linter":
                hook["priority"] = LINTER_PRIORITY
            case None:
                ...
            case never:
                assert_never(never)
        re_insert_hook_dict(hook, repo)


if __name__ == "__main__":
    _main()
