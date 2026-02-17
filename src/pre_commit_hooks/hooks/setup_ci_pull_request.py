from __future__ import annotations

from functools import partial
from hashlib import blake2b
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS, ListStrs, SecretStr, Str, option
from utilities.core import always_iterable, extract_groups, is_pytest
from utilities.pydantic import extract_secret
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    CI_OS,
    GITEA_PULL_REQUEST_YAML,
    GITHUB_PULL_REQUEST_YAML,
    MAX_PYTHON_VERSION,
    PYTHON_VERSION,
    certificates_option,
    gitea_option,
    paths_argument,
    repo_name_option,
    token_checkout_option,
    token_github_option,
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

    from utilities.types import MaybeSequenceStr, PathLike, SecretLike, StrDict


@command(**CONTEXT_SETTINGS)
@paths_argument
@gitea_option
@repo_name_option
@certificates_option
@token_checkout_option
@token_github_option
@option("--pyright-python-version", type=Str(), default=None)
@option("--index", type=ListStrs(), default=None)
@option("--pyright-resolution", type=Str(), default=None)
@option("--pyright-prerelease", type=Str(), default=None)
@option("--pytest-runs-on", type=ListStrs(), default=None)
@option("--pytest-sops-age-key", type=SecretStr(), default=None)
@option("--pytest-os", type=ListStrs(), default=None)
@option("--pytest-python-version", type=Str(), default=None)
def _main(
    *,
    paths: tuple[Path, ...],
    gitea: bool,
    repo_name: str | None,
    certificates: bool,
    token_checkout: SecretLike | None,
    token_github: SecretLike | None,
    pyright_python_version: str | None,
    index: MaybeSequenceStr | None,
    pyright_resolution: str | None,
    pyright_prerelease: str | None,
    pytest_runs_on: MaybeSequenceStr | None,
    pytest_sops_age_key: SecretLike | None,
    pytest_os: MaybeSequenceStr | None,
    pytest_python_version: str | None,
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
            token_checkout=token_checkout,
            token_github=token_github,
            pyright_python_version=pyright_python_version,
            index=index,
            pyright_resolution=pyright_resolution,
            pyright_prerelease=pyright_prerelease,
            pytest_runs_on=pytest_runs_on,
            pytest_sops_age_key=pytest_sops_age_key,
            pytest_os=pytest_os,
            pytest_python_version=pytest_python_version,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    repo_name: str | None = None,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    pyright_python_version: str | None = None,
    index: MaybeSequenceStr | None = None,
    pyright_resolution: str | None = None,
    pyright_prerelease: str | None = None,
    pytest_runs_on: MaybeSequenceStr | None = None,
    pytest_sops_age_key: SecretLike | None = None,
    pytest_os: MaybeSequenceStr | None = None,
    pytest_python_version: str | None = None,
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
        token_checkout=token_checkout,
        token_github=token_github,
        python_version=pyright_python_version,
        index=index,
        resolution=pyright_resolution,
        prerelease=pyright_prerelease,
    )
    _add_pytest(
        path=path,
        modifications=modifications,
        runs_on=pytest_runs_on,
        certificates=certificates,
        token_checkout=token_checkout,
        token_github=token_github,
        sops_age_key=pytest_sops_age_key,
        index=index,
        prerelease=pyright_prerelease,
        os=pytest_os,
        python_version=pytest_python_version,
    )
    _add_ruff(
        path=path,
        modifications=modifications,
        certificates=certificates,
        token_checkout=token_checkout,
        token_github=token_github,
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
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    python_version: str | None = None,
    index: MaybeSequenceStr | None = None,
    resolution: str | None = None,
    prerelease: str | None = None,
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
        if token_checkout is not None:
            with_["token-checkout"] = extract_secret(token_checkout)
        if token_github is not None:
            with_["token-github"] = extract_secret(token_github)
        if python_version is not None:
            with_["python-version"] = python_version
        if index is not None:
            with_["index"] = ",".join(always_iterable(index))
        if resolution is not None:
            with_["resolution"] = resolution
        if prerelease is not None:
            with_["prerelease"] = prerelease
        if certificates:
            with_["native-tls"] = True


def _add_pytest(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    runs_on: MaybeSequenceStr | None = None,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    sops_age_key: SecretLike | None = None,
    index: MaybeSequenceStr | None = None,
    prerelease: str | None = None,
    os: MaybeSequenceStr | None = None,
    python_version: MaybeSequenceStr | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        pytest = get_set_dict(jobs, "pytest")
        env = get_set_dict(pytest, "env")
        env["CI"] = "1"
        pytest["name"] = (
            "pytest (${{matrix.os}}, ${{matrix.python-version}}, ${{matrix.resolution}})"
        )
        runs_on_list = get_set_list_strs(pytest, "runs-on")
        ensure_contains(runs_on_list, "${{matrix.os}}")
        if runs_on is not None:
            ensure_contains(runs_on_list, *always_iterable(runs_on))
        steps = get_set_list_dicts(pytest, "steps")
        if certificates:
            _add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'pytest'", "uses": "dycw/action-pytest@latest"}
        )
        with_ = get_set_dict(step, "with")
        if token_checkout is not None:
            with_["token-checkout"] = extract_secret(token_checkout)
        if token_github is not None:
            with_["token-github"] = extract_secret(token_github)
        with_["python-version"] = "${{matrix.python-version}}"
        if sops_age_key is not None:
            with_["sops-age-key"] = extract_secret(sops_age_key)
        if index is not None:
            with_["index"] = ",".join(always_iterable(index))
        with_["resolution"] = "${{matrix.resolution}}"
        if prerelease is not None:
            with_["prerelease"] = prerelease
        if certificates:
            with_["native-tls"] = True
        strategy = get_set_dict(pytest, "strategy")
        strategy["fail-fast"] = False
        matrix = get_set_dict(strategy, "matrix")
        os_list = get_set_list_strs(matrix, "os")
        ensure_contains(os_list, *always_iterable(CI_OS if os is None else os))
        python_version_list = get_set_list_strs(matrix, "python-version")
        if python_version is None:
            ensure_contains(python_version_list, *_yield_python_versions())
        else:
            ensure_contains(python_version_list, *always_iterable(python_version))
        resolution_list = get_set_list_strs(matrix, "resolution")
        ensure_contains(resolution_list, "highest", "lowest-direct")
        pytest["timeout-minutes"] = 10


def _add_ruff(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        ruff = get_set_dict(jobs, "ruff")
        ruff["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(ruff, "steps")
        if certificates:
            _add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps, {"name": "Run 'ruff'", "uses": "dycw/action-ruff@latest"}
        )
        with_ = get_set_dict(step, "with")
        if token_checkout is not None:
            with_["token-checkout"] = extract_secret(token_checkout)
        if token_github is not None:
            with_["token-github"] = extract_secret(token_github)


def _add_update_certificates(steps: list[StrDict], /) -> None:
    ensure_contains(
        steps, {"name": "Update CA certificates", "run": "sudo update-ca-certificates"}
    )


def _yield_python_versions(
    *, version: str = PYTHON_VERSION, max_: str = MAX_PYTHON_VERSION
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
