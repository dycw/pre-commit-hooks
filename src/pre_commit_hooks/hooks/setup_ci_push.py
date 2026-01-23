from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    GITEA_PUSH_YAML,
    GITHUB_PULL_REQUEST_YAML,
    GITHUB_PUSH_YAML,
    certificates_option,
    ci_tag_all_option,
    gitea_option,
    paths_argument,
    python_option,
)
from pre_commit_hooks.utilities import (
    add_update_certificates,
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
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@gitea_option
@certificates_option
@ci_tag_all_option
@python_option
def _main(
    *,
    paths: tuple[Path, ...],
    gitea: bool = False,
    certificates: bool = False,
    ci_tag_all: bool = False,
    python: bool = False,
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(
        *paths, target=GITEA_PUSH_YAML if gitea else GITHUB_PUSH_YAML
    )
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            certificates=certificates,
            tag_all=ci_tag_all,
            python=python,
            gitea=gitea,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    certificates: bool = False,
    tag_all: bool = False,
    python: bool = False,
    gitea: bool = False,
) -> bool:
    modifications: set[Path] = set()
    _add_header(path=path, modifications=modifications)
    _add_tag(
        path=path, modifications=modifications, certificates=certificates, all_=tag_all
    )
    if python:
        _add_publish(
            path=path,
            modifications=modifications,
            gitea=gitea,
            certificates=certificates,
        )
    return len(modifications) == 0


def _add_header(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        dict_["name"] = "push"
        on = get_set_dict(dict_, "on")
        push = get_set_dict(on, "push")
        branches = get_set_list_strs(push, "branches")
        ensure_contains(branches, "master")


def _add_tag(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    certificates: bool = False,
    all_: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        tag = get_set_dict(jobs, "tag")
        tag["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(tag, "steps")
        if certificates:
            add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps,
            {"name": "Tag the latest commit", "uses": "dycw/action-tag-commit@latest"},
        )
        if all_:
            with_ = get_set_dict(step, "with")
            with_["major-minor"] = True
            with_["major"] = True
            with_["latest"] = True


def _add_publish(
    *,
    path: PathLike = GITHUB_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
    gitea: bool = False,
    certificates: bool = False,
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
        if certificates:
            add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps,
            {
                "name": "Build and publish the package",
                "uses": "dycw/action-publish-package@latest",
            },
        )
        with_ = get_set_dict(step, "with")
        if certificates:
            with_["native-tls"] = True


if __name__ == "__main__":
    _main()
