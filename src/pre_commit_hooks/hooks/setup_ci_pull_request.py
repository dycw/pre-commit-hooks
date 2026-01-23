from __future__ import annotations

from functools import partial
from hashlib import blake2b
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import always_iterable, extract_groups, is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    GITEA_PULL_REQUEST_YAML,
    GITHUB_PULL_REQUEST_YAML,
    MAX_PYTHON_VERSION,
    PYTHON_VERSION,
    certificates_option,
    ci_pytest_os_option,
    ci_pytest_python_version_option,
    ci_pytest_runs_on_option,
    gitea_option,
    paths_argument,
    python_version_option,
    repo_name_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    ensure_contains_partial_dict,
    get_set_dict,
    get_set_list_dicts,
    get_set_list_strs,
    merge_paths,
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
@repo_name_option
@certificates_option
@python_version_option
@ci_pytest_runs_on_option
@ci_pytest_os_option
@ci_pytest_python_version_option
def _main(
    *,
    paths: tuple[Path, ...],
    gitea: bool = False,
    repo_name: str | None = None,
    certificates: bool = False,
    python_version: str | None = None,
    ci_pytest_runs_on: MaybeSequenceStr | None = None,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_python_version: MaybeSequenceStr | None = None,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(
        *paths, target=GITEA_PULL_REQUEST_YAML if gitea else GITHUB_PULL_REQUEST_YAML
    )
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            repo_name=repo_name,
            certificates=certificates,
            python_version=python_version,
            ci_pytest_runs_on=ci_pytest_runs_on,
            ci_pytest_os=ci_pytest_os,
            ci_pytest_python_version=ci_pytest_python_version,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    repo_name: str | None = None,
    certificates: bool = False,
    python_version: str | None = None,
    ci_pytest_runs_on: MaybeSequenceStr | None = None,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_python_version: MaybeSequenceStr | None = None,
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
        certificates=certificates,
        version=python_version,
    )
    _add_pytest(
        path=path,
        modifications=modifications,
        ci_runs_on=ci_pytest_runs_on,
        certificates=certificates,
        ci_os=ci_pytest_os,
        ci_python_version=ci_pytest_python_version,
        version=python_version,
    )
    _add_ruff(path=path, modifications=modifications, certificates=certificates)
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
    certificates: bool = False,
    version: str | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        pyright = get_set_dict(jobs, "pyright")
        pyright["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(pyright, "steps")
        if certificates:
            _add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'pyright'", "uses": "dycw/action-pyright@latest"}
        )
        with_ = get_set_dict(step, "with")
        with_["python-version"] = PYTHON_VERSION if version is None else version
        if certificates:
            with_["native-tls"] = True


def _add_pytest(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    ci_runs_on: MaybeSequenceStr | None = None,
    certificates: bool = False,
    ci_os: MaybeSequenceStr | None = None,
    ci_python_version: MaybeSequenceStr | None = None,
    version: str | None = None,
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
        ensure_contains(runs_on, "${{matrix.os}}")
        if ci_runs_on is not None:
            ensure_contains(runs_on, *always_iterable(ci_runs_on))
        steps = get_set_list_dicts(pytest, "steps")
        if certificates:
            _add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'pytest'", "uses": "dycw/action-pytest@latest"}
        )
        with_ = get_set_dict(step, "with")
        with_["python-version"] = "${{matrix.python-version}}"
        with_["resolution"] = "${{matrix.resolution}}"
        if certificates:
            with_["native-tls"] = True
        strategy = get_set_dict(pytest, "strategy")
        strategy["fail-fast"] = False
        matrix = get_set_dict(strategy, "matrix")
        os = get_set_list_strs(matrix, "os")
        if ci_os is None:
            ci_os_use = ["macos-latest", "ubuntu-latest"]
        else:
            ci_os_use = list(always_iterable(ci_os))
        ensure_contains(os, *ci_os_use)
        python_version_dict = get_set_list_strs(matrix, "python-version")
        if ci_python_version is None:
            ci_python_version_use = list(_yield_python_versions(version=version))
        else:
            ci_python_version_use = list(always_iterable(ci_python_version))
        ensure_contains(python_version_dict, *ci_python_version_use)
        resolution = get_set_list_strs(matrix, "resolution")
        ensure_contains(resolution, "highest", "lowest-direct")
        pytest["timeout-minutes"] = 10


def _add_ruff(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    certificates: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        ruff = get_set_dict(jobs, "ruff")
        ruff["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(ruff, "steps")
        if certificates:
            _add_update_certificates(steps)
        _ = ensure_contains_partial_dict(
            steps, {"name": "Run 'ruff'", "uses": "dycw/action-ruff@latest"}
        )


def _add_update_certificates(steps: list[StrDict], /) -> None:
    ensure_contains(
        steps, {"name": "Update CA certificates", "run": "sudo update-ca-certificates"}
    )


def _yield_python_versions(
    *, version: str | None = None, max_: str = MAX_PYTHON_VERSION
) -> Iterator[str]:
    version_use = PYTHON_VERSION if version is None else version
    major, minor = _extract_python_version_tuple(version_use)
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
