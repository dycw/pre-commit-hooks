from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    GITEA_PUSH_YAML,
    GITHUB_PULL_REQUEST_YAML,
    GITHUB_PUSH_YAML,
    gitea_option,
    paths_argument,
    python_uv_native_tls_option,
)
from pre_commit_hooks.utilities import (
    add_update_certificates,
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

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@gitea_option
@python_uv_native_tls_option
def _main(
    *, paths: tuple[Path, ...], gitea: bool = False, python_uv_native_tls: bool = False
) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p.parent / (GITEA_PUSH_YAML if gitea else GITHUB_PUSH_YAML),
            gitea=gitea,
            uv_native_tls=python_uv_native_tls,
        )
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    gitea: bool = False,
    uv_native_tls: bool = False,
) -> bool:
    modifications: set[Path] = set()
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        dict_["name"] = "push"
        on = get_set_dict(dict_, "on")
        push = get_set_dict(on, "push")
        branches = get_set_list_strs(push, "branches")
        ensure_contains(branches, "master")
    _add_publish(
        path=path, modifications=modifications, gitea=gitea, uv_native_tls=uv_native_tls
    )
    _add_tag(path=path, modifications=modifications, uv_native_tls=uv_native_tls)
    return len(modifications) == 0


def _add_publish(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    gitea: bool = False,
    uv_native_tls: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        publish = get_set_dict(jobs, "publish")
        if not gitea:
            environment = get_set_dict(publish, "environment")
            environment["name"] = "pypi"
            permissions = get_set_dict(publish, "permissions")
            permissions["id-token"] = "write"
        publish["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(publish, "steps")
        if uv_native_tls:
            add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps,
            {
                "name": "Build and publish the package",
                "uses": "dycw/action-publish-package@latest",
            },
        )
        with_ = get_set_dict(step, "with")
        if uv_native_tls:
            with_["native-tls"] = True


def _add_tag(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    uv_native_tls: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        tag = get_set_dict(jobs, "tag")
        tag["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(tag, "steps")
        if uv_native_tls:
            add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps,
            {"name": "Tag the latest commit", "uses": "dycw/action-tag-commit@latest"},
        )
        with_ = get_set_dict(step, "with")
        if uv_native_tls:
            with_["native-tls"] = True


if __name__ == "__main__":
    _main()
