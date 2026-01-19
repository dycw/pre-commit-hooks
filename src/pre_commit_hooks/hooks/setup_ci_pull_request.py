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
from utilities.iterables import always_iterable
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
    MAX_PYTHON_VERSION,
    ci_pytest_os_option,
    ci_pytest_python_version_option,
    ci_pytest_runs_on_option,
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
    from collections.abc import Callable, Iterator, MutableSet
    from pathlib import Path

    from utilities.types import MaybeSequenceStr, PathLike, StrDict


@command(**CONTEXT_SETTINGS)
@paths_argument
@gitea_option
@ci_pytest_os_option
@ci_pytest_python_version_option
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
    ci_pytest_python_version: MaybeSequenceStr | None = None,
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
            pytest_python_version=ci_pytest_python_version,
            python_version=python_version,
            uv_native_tls=python_uv_native_tls,
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
    pytest_python_version: MaybeSequenceStr | None = None,
    pytest_runs_on: MaybeSequenceStr | None = None,
    python_version: str = DEFAULT_PYTHON_VERSION,
    uv_native_tls: bool = False,
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
    _add_pyright(
        path=path,
        modifications=modifications,
        python_version=python_version,
        uv_native_tls=uv_native_tls,
    )
    _add_pytest(
        path=path,
        modifications=modifications,
        pytest_os=pytest_os,
        pytest_runs_on=pytest_runs_on,
        pytest_python_version=pytest_python_version,
        python_version=python_version,
        uv_native_tls=uv_native_tls,
    )
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
            uv_native_tls=uv_native_tls,
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
    uv_native_tls: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        pyright = get_set_dict(jobs, "pyright")
        pyright["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(pyright, "steps")
        if uv_native_tls:
            _add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'pyright'", "uses": "dycw/action-pyright@latest"}
        )
        with_ = get_set_dict(step, "with")
        with_["python-version"] = python_version
        if uv_native_tls:
            with_["native-tls"] = True


def _add_pytest(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    pytest_os: MaybeSequenceStr | None = None,
    pytest_python_version: MaybeSequenceStr | None = None,
    pytest_runs_on: MaybeSequenceStr | None = None,
    python_version: str = DEFAULT_PYTHON_VERSION,
    uv_native_tls: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        pytest = get_set_dict(jobs, "pytest")
        env = get_set_dict(pytest, "env")
        env["CI"] = "1"
        pytest["name"] = (
            "pytest (${{matrix.os}}, ${{matrix.python-version}}, ${{matrix.resolution}})"
        )
        runs_on = get_set_list_strs(pytest, "runs-on")
        if pytest_runs_on is not None:
            ensure_contains(runs_on, *always_iterable(pytest_runs_on))
        steps = get_set_list_dicts(pytest, "steps")
        if uv_native_tls:
            _add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'pytest'", "uses": "dycw/action-pytest@latest"}
        )
        with_ = get_set_dict(step, "with")
        with_["python-version"] = "${{matrix.python-version}}"
        with_["resolution"] = "${{matrix.resolution}}"
        if uv_native_tls:
            with_["native-tls"] = True
        strategy = get_set_dict(pytest, "strategy")
        strategy["fail-fast"] = False
        matrix = get_set_dict(strategy, "matrix")
        os = get_set_list_strs(matrix, "os")
        if pytest_os is None:
            pytest_os_use = ["macos-latest", "ubuntu-latest"]
        else:
            pytest_os_use = list(always_iterable(pytest_os))
        ensure_contains(os, *pytest_os_use)
        python_version_dict = get_set_list_strs(matrix, "python-version")
        if pytest_python_version is None:
            pytest_python_version_use = list(
                _yield_python_versions(version=python_version)
            )
        else:
            pytest_python_version_use = list(always_iterable(pytest_python_version))
        ensure_contains(python_version_dict, *pytest_python_version_use)
        resolution = get_set_list_strs(matrix, "resolution")
        ensure_contains(resolution, "highest", "lowest-direct")
        pytest["timeout-minutes"] = 10


def _add_update_certificates(steps: list[StrDict], /) -> None:
    ensure_contains(
        steps, {"name": "Update CA certificates", "run": "sudo update-ca-certificates"}
    )


def _yield_python_versions(
    *, version: str = DEFAULT_PYTHON_VERSION, max_: str = MAX_PYTHON_VERSION
) -> Iterator[str]:
    major, minor = _extract_python_version_tuple(version)
    max_major, max_minor = _extract_python_version_tuple(max_)
    if major != max_major:
        msg = f"Major versions must be equal; got {major} and {max_major}"
        raise ValueError(msg)
    if minor > max_minor:
        msg = f"Minor version must be at most {max_minor}; got {minor}"
        raise ValueError(msg)
    for i in range(minor, max_minor + 1):
        yield f"{major}.{i}"


def _extract_python_version_tuple(version: str, /) -> tuple[int, int]:
    major, minor = extract_groups(r"^(\d+)\.(\d+)$", version)
    return int(major), int(minor)


if __name__ == "__main__":
    _main()
