from __future__ import annotations

from functools import partial
from hashlib import blake2b
from pathlib import Path
from re import MULTILINE, sub
from typing import TYPE_CHECKING

from click import command, option
from utilities.click import CONTEXT_SETTINGS
from utilities.functions import get_func_name
from utilities.inflect import counted_noun
from utilities.os import is_pytest
from utilities.re import extract_groups
from utilities.subprocess import ripgrep
from utilities.text import repr_str
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    DEFAULT_PYTHON_VERSION,
    ENVRC,
    GITEA_PULL_REQUEST_YAML,
    GITHUB_PULL_REQUEST_YAML,
    ci_pytest_os_option,
    ci_pytest_runs_on_option,
    ci_pytest_version_option,
    gitea_option,
    paths_argument,
    python_option,
    python_uv_index_option,
    python_uv_native_tls_option,
    python_version_option,
    repo_name_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    ensure_contains_partial_dict,
    get_set_dict,
    get_set_list_dicts,
    get_set_list_strs,
    run_all_maybe_raise,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@gitea_option
@ci_pytest_os_option
@ci_pytest_version_option
@ci_pytest_runs_on_option
@python_uv_native_tls_option
@python_version_option
@repo_name_option
def _main(
    *,
    paths: tuple[Path, ...],
    gitea: bool = False,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_runs_on: MaybeSequenceStr | None = None,
    ci_pytest_version: MaybeSequenceStr | None = None,
    python_uv_native_tls: bool = False,
    python_version: str = DEFAULT_PYTHON_VERSION,
    repo_name: str | None = None,
) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p.parent
            / (GITEA_PULL_REQUEST_YAML if gitea else GITHUB_PULL_REQUEST_YAML),
            gitea=gitea,
            pytest_os=ci_pytest_os,
            pytest_runs_on=ci_pytest_runs_on,
            pytest_version=ci_pytest_version,
            python_uv_native_tls=python_uv_native_tls,
            python_version=python_version,
            repo_name=repo_name,
        )
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    gitea: bool = False,
    pytest_os: MaybeSequenceStr | None = None,
    pytest_version: MaybeSequenceStr | None = None,
    pytest_runs_on: MaybeSequenceStr | None = None,
    python_uv_native_tls: bool = False,
    python_version: str = DEFAULT_PYTHON_VERSION,
    repo_name: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        dict_["name"] = "pull-request"
        on = get_set_dict(dict_, "on")
        pull_request = get_set_dict(on, "pull_request")
        branches = get_set_list_strs(pull_request, "branches")
        ensure_contains(branches, "master")
        schedule = get_set_list_dicts(on, "schedule")
        ensure_contains(schedule, {"cron": _get_cron_job(repo_name=repo_name)})
    _add_pyright(path=path, modifications=modifications, python_version=python_version)

    if ruff:
        ruff_dict = get_set_dict(jobs, "ruff")
        ruff_dict["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(ruff_dict, "steps")
        if certificates:
            ensure_contains(steps, update_ca_certificates_dict("steps"))
        ensure_contains(
            steps,
            action_ruff_dict(token_checkout=token_checkout, token_github=token_github),
        )
    with yield_text_file(path, modifications=modifications) as context:
        text = strip_and_dedent("""
            #!/usr/bin/env sh
            # shellcheck source=/dev/null

            # echo
            echo_date() { echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2; }
        """)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"
    if python:
        _add_python(
            path=path,
            modifications=modifications,
            uv_index=python_uv_index,
            uv_native_tls=python_uv_native_tls,
            version=python_version,
        )
    return len(modifications) == 0


def _get_cron_job(*, repo_name: str | None = None) -> str:
    if repo_name is None:
        minute = hour = 0
    else:
        digest = blake2b(repo_name.encode(), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        minute = value % 60
        hour = (value // 60) % 24
    return f"{minute} {hour} * * *"


def _add_pyright(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    python_version: str = DEFAULT_PYTHON_VERSION,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        pyright = get_set_dict(jobs, "pyright")
        pyright["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(pyright, "steps")
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'pyright'", "uses": "dycw/action-pyright@latest"}
        )
        with_ = get_set_dict(step, "with")
        with_["python-version"] = python_version


def _add_pytest(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    pytest_os: MaybeSequenceStr | None = None,
    pytest_runs_on: MaybeSequenceStr | None = None,
    pytest_version: MaybeSequenceStr | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        pytest_dict = get_set_dict(jobs, "pytest")
        env = get_set_dict(pytest_dict, "env")
        env["CI"] = "1"
        pytest_dict["name"] = (
            "pytest (${{matrix.os}}, ${{matrix.python-version}}, ${{matrix.resolution}})"
        )
        pytest_dict["runs-on"] = "${{matrix.os}}"
        steps = get_set_list_dicts(pytest_dict, "steps")
        if certificates:
            ensure_contains(steps, update_ca_certificates_dict("pytest"))
        ensure_contains(
            steps,
            action_pytest_dict(
                token_checkout=token_checkout,
                token_github=token_github,
                python_version="${{matrix.python-version}}",
                sops_age_key=pytest__sops_age_key,
                resolution="${{matrix.resolution}}",
                native_tls=uv__native_tls,
            ),
        )
        strategy_dict = get_set_dict(pytest_dict, "strategy")
        strategy_dict["fail-fast"] = False
        matrix = get_set_dict(strategy_dict, "matrix")
        os = get_set_list_strs(matrix, "os")
        if pytest__macos:
            ensure_contains(os, "macos-latest")
        if pytest__ubuntu:
            ensure_contains(os, "ubuntu-latest")
        if pytest__windows:
            ensure_contains(os, "windows-latest")
        python_version_dict = get_set_list_strs(matrix, "python-version")
        if pytest__all_versions:
            ensure_contains(python_version_dict, *yield_python_versions(python_version))
        else:
            ensure_contains(python_version_dict, python_version)
        resolution = get_set_list_strs(matrix, "resolution")
        ensure_contains(resolution, "highest", "lowest-direct")
        if pytest__timeout is not None:
            pytest_dict["timeout-minutes"] = max(round(pytest__timeout / 60), 1)


if __name__ == "__main__":
    _main()
