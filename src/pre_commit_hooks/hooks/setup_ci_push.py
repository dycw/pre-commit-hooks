from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS, ListStrs, SecretStr, Str, flag, option
from utilities.core import always_iterable, is_pytest
from utilities.pydantic import extract_secret
from utilities.types import PathLike

from pre_commit_hooks.click import (
    certificates_flag,
    gitea_flag,
    paths_argument,
    token_checkout_option,
    token_github_option,
)
from pre_commit_hooks.constants import GITEA_PUSH_YAML, GITHUB_PUSH_YAML
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

    from utilities.types import MaybeSequenceStr, PathLike, SecretLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@gitea_flag
@certificates_flag
@token_checkout_option
@token_github_option
@option("--tag-user-name", type=Str(), default=None)
@option("--tag-user-email", type=Str(), default=None)
@flag("--tag-major-minor", default=False)
@flag("--tag-major", default=False)
@flag("--tag-latest", default=False)
@flag("--package", default=False)
@option("--package-job-name-suffix", type=Str(), default=None)
@option("--package-username", type=Str(), default=None)
@option("--package-password", type=SecretStr(), default=None)
@option("--package-publish-url", type=Str(), default=None)
@flag("--package-trusted-publishing", default=False)
@flag("--image", default=False)
@option("--image-runs-on", type=Str(), default=None)
@option("--image-registry-host", type=Str(), default=None)
@option("--image-registry-port", type=int, default=None)
@option("--image-registry-username", type=Str(), default=None)
@option("--image-registry-password", type=SecretStr(), default=None)
@option("--image-namespace", type=Str(), default=None)
@option("--image-uv-index", type=ListStrs(), default=None)
@option("--image-uv-index-username", type=Str(), default=None)
@option("--image-uv-index-password", type=SecretStr(), default=None)
def _main(
    *,
    paths: tuple[Path, ...],
    gitea: bool,
    certificates: bool,
    token_checkout: SecretLike | None,
    token_github: SecretLike | None,
    tag_user_name: str | None,
    tag_user_email: str | None,
    tag_major_minor: bool,
    tag_major: bool,
    tag_latest: bool,
    package: bool,
    package_job_name_suffix: str | None,
    package_username: str | None,
    package_password: SecretLike | None,
    package_publish_url: str | None,
    package_trusted_publishing: bool,
    image: bool,
    image_runs_on: MaybeSequenceStr | None,
    image_registry_host: str | None,
    image_registry_port: int | None,
    image_registry_username: str | None,
    image_registry_password: SecretLike | None,
    image_namespace: str | None,
    image_uv_index: MaybeSequenceStr | None,
    image_uv_index_username: str | None,
    image_uv_index_password: SecretLike | None,
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
            token_checkout=token_checkout,
            token_github=token_github,
            tag_user_name=tag_user_name,
            tag_user_email=tag_user_email,
            tag_major_minor=tag_major_minor,
            tag_major=tag_major,
            tag_latest=tag_latest,
            package=package,
            package_add_env_and_perms=not gitea,
            package_job_name_suffix=package_job_name_suffix,
            package_username=package_username,
            package_password=package_password,
            package_publish_url=package_publish_url,
            package_trusted_publishing=package_trusted_publishing,
            image=image,
            image_runs_on=image_runs_on,
            image_registry_host=image_registry_host,
            image_registry_port=image_registry_port,
            image_registry_username=image_registry_username,
            image_registry_password=image_registry_password,
            image_namespace=image_namespace,
            image_uv_index=image_uv_index,
            image_uv_index_username=image_uv_index_username,
            image_uv_index_password=image_uv_index_password,
        )
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = GITHUB_PUSH_YAML,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    tag_user_name: str | None = None,
    tag_user_email: str | None = None,
    tag_major_minor: bool = False,
    tag_major: bool = False,
    tag_latest: bool = False,
    package: bool = False,
    package_job_name_suffix: str | None = None,
    package_add_env_and_perms: bool = False,
    package_username: str | None = None,
    package_password: SecretLike | None = None,
    package_publish_url: str | None = None,
    package_trusted_publishing: bool = False,
    image: bool = False,
    image_runs_on: MaybeSequenceStr | None = None,
    image_registry_host: str | None = None,
    image_registry_port: int | None = None,
    image_registry_username: str | None = None,
    image_registry_password: SecretLike | None = None,
    image_namespace: str | None = None,
    image_uv_index: MaybeSequenceStr | None = None,
    image_uv_index_username: str | None = None,
    image_uv_index_password: SecretLike | None = None,
) -> bool:
    modifications: set[Path] = set()
    _add_header(path=path, modifications=modifications)
    _add_tag(
        path=path,
        modifications=modifications,
        certificates=certificates,
        token_checkout=token_checkout,
        token_github=token_github,
        user_name=tag_user_name,
        user_email=tag_user_email,
        major_minor=tag_major_minor,
        major=tag_major,
        latest=tag_latest,
    )
    if package:
        _add_publish_package(
            path=path,
            modifications=modifications,
            job_name_suffix=package_job_name_suffix,
            add_env_and_perms=package_add_env_and_perms,
            certificates=certificates,
            token_checkout=token_checkout,
            token_github=token_github,
            username=package_username,
            password=package_password,
            publish_url=package_publish_url,
            trusted_publishing=package_trusted_publishing,
        )
    if image:
        _add_publish_image(
            path=path,
            modifications=modifications,
            runs_on=image_runs_on,
            certificates=certificates,
            token_checkout=token_checkout,
            token_github=token_github,
            registry_host=image_registry_host,
            registry_port=image_registry_port,
            registry_username=image_registry_username,
            registry_password=image_registry_password,
            namespace=image_namespace,
            uv_index=image_uv_index,
            uv_index_username=image_uv_index_username,
            uv_index_password=image_uv_index_password,
        )
    return len(modifications) == 0


def _add_header(
    *, path: PathLike = GITHUB_PUSH_YAML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        dict_["name"] = "push"
        on = get_set_dict(dict_, "on")
        push = get_set_dict(on, "push")
        branches = get_set_list_strs(push, "branches")
        ensure_contains(branches, "master")


def _add_tag(
    *,
    path: PathLike = GITHUB_PUSH_YAML,
    modifications: MutableSet[Path] | None = None,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    user_name: str | None = None,
    user_email: str | None = None,
    major_minor: bool = False,
    major: bool = False,
    latest: bool = False,
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
        with_ = get_set_dict(step, "with")
        if token_checkout is not None:
            with_["token-checkout"] = extract_secret(token_checkout)
        if token_github is not None:
            with_["token-github"] = extract_secret(token_github)
        if user_name is not None:
            with_["user-name"] = user_name
        if user_email is not None:
            with_["user-name"] = user_email
        if major_minor:
            with_["major-minor"] = True
        if major:
            with_["major"] = True
        if latest:
            with_["latest"] = True


def _add_publish_package(
    *,
    path: PathLike = GITHUB_PUSH_YAML,
    modifications: MutableSet[Path] | None = None,
    job_name_suffix: str | None = None,
    add_env_and_perms: bool = False,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    username: str | None = None,
    password: SecretLike | None = None,
    publish_url: str | None = None,
    trusted_publishing: bool = False,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        job_name = "publish-package"
        if job_name_suffix is not None:
            job_name = f"{job_name}-{job_name_suffix}"
        publish_package = get_set_dict(jobs, job_name)
        if add_env_and_perms:
            environment = get_set_dict(publish_package, "environment")
            environment["name"] = "pypi"
            permissions = get_set_dict(publish_package, "permissions")
            permissions["id-token"] = "write"
        publish_package["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(publish_package, "steps")
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
        if token_checkout is not None:
            with_["token-checkout"] = extract_secret(token_checkout)
        if token_github is not None:
            with_["token-github"] = extract_secret(token_github)
        if username is not None:
            with_["username"] = username
        if password is not None:
            with_["password"] = extract_secret(password)
        if publish_url is not None:
            with_["publish_url"] = publish_url
        if trusted_publishing:
            with_["trusted-publishing"]
        if certificates:
            with_["native-tls"] = True


def _add_publish_image(
    *,
    path: PathLike = GITHUB_PUSH_YAML,
    modifications: MutableSet[Path] | None = None,
    runs_on: MaybeSequenceStr | None = None,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    registry_host: str | None = None,
    registry_port: int | None = None,
    registry_username: str | None = None,
    registry_password: SecretLike | None = None,
    namespace: str | None = None,
    uv_index: MaybeSequenceStr | None = None,
    uv_index_username: str | None = None,
    uv_index_password: SecretLike | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        publish_image = get_set_dict(jobs, "publish-image")
        runs_on = get_set_list_strs(publish_image, "runs-on")
        ensure_contains(runs_on, "ubuntu-latest")
        if runs_on is not None:
            ensure_contains(runs_on, *always_iterable(runs_on))
        steps = get_set_list_dicts(publish_image, "steps")
        if certificates:
            add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps,
            {
                "name": "Build and publish the image",
                "uses": "dycw/action-publish-image@latest",
            },
        )
        with_ = get_set_dict(step, "with")
        if token_checkout is not None:
            with_["token-checkout"] = extract_secret(token_checkout)
        if token_github is not None:
            with_["token-github"] = extract_secret(token_github)
        if registry_host is not None:
            with_["registry-host"] = registry_host
        if registry_port is not None:
            with_["registry-port"] = registry_port
        if registry_username is not None:
            with_["registry-username"] = registry_username
        if registry_password is not None:
            with_["registry-password"] = extract_secret(registry_password)
        if namespace is not None:
            with_["namespace"] = namespace
        if uv_index is not None:
            with_["uv-index"] = ",".join(always_iterable(uv_index))
        if uv_index_username is not None:
            with_["uv-index-username"] = uv_index_username
        if uv_index_password is not None:
            with_["uv-index-password"] = extract_secret(uv_index_password)
        if certificates:
            with_["native-tls"] = True


if __name__ == "__main__":
    _main()
