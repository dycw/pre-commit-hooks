from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Literal, assert_never, overload
from urllib.parse import urlsplit, urlunsplit

from click import command
from utilities.click import (
    CONTEXT_SETTINGS,
    ListStrs,
    SecretStr,
    Str,
    flag,
    option,
    to_args,
)
from utilities.core import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.click import (
    certificates_flag,
    description_option,
    paths_argument,
    python_flag,
    python_version_option,
    repo_name_option,
)
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
    PYTEST_TOML,
    RUFF_URL,
    SHELLCHECK_URL,
    SHFMT_URL,
    STD_PRE_COMMIT_HOOKS_URL,
    STYLUA_URL,
    TAPLO_URL,
    XMLFORMATTER_URL,
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

    from utilities.types import MaybeSequenceStr, PathLike, SecretLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@certificates_flag
@flag("--ci-github", default=False)
@flag("--ci-gitea", default=False)
@flag("--ci-image", default=False)
@option("--ci-image-registry-host", type=Str(), default=None)
@option("--ci-image-registry-port", type=int, default=None)
@option("--ci-image-registry-username", type=Str(), default=None)
@option("--ci-image-registry-password", type=SecretStr(), default=None)
@option("--ci-image-namespace", type=Str(), default=None)
@option("--ci-package-job-name-suffix", type=Str(), default=None)
@flag("--ci-package-trusted-publishing", default=False)
@option("--ci-pyright-prerelease", type=Str(), default=None)
@option("--ci-pyright-resolution", type=Str(), default=None)
@option("--ci-pytest-os", type=ListStrs(), default=None)
@option("--ci-pytest-python-version", type=ListStrs(), default=None)
@option("--ci-pytest-sops-age-key", type=SecretStr(), default=None)
@option("--ci-runs-on", type=ListStrs(), default=None)
@option("--ci-tag-user-name", type=Str(), default=None)
@option("--ci-tag-user-email", type=Str(), default=None)
@flag("--ci-tag-all", default=False)
@option("--ci-token-checkout", type=SecretStr(), default=None)
@option("--ci-token-github", type=SecretStr(), default=None)
@description_option
@flag("--direnv", default=False)
@flag("--docker", default=False)
@flag("--fish", default=False)
@flag("--just", default=False)
@flag("--lua", default=False)
@flag("--prettier", default=False)
@python_flag
@option("--python-index-name", type=Str(), default=None)
@option("--python-index-url", type=Str(), default=None)
@option("--python-index-username", type=Str(), default=None)
@option("--python-index-password-read", type=SecretStr(), default=None)
@option("--python-index-password-write", type=SecretStr(), default=None)
@option("--python-package-name-external", type=Str(), default=None)
@option("--python-package-name-internal", type=Str(), default=None)
@python_version_option
@repo_name_option
@flag("--shell", default=False)
@flag("--toml", default=False)
@flag("--xml", default=False)
def _main(
    *,
    paths: tuple[Path, ...],
    certificates: bool,
    ci_github: bool,
    ci_gitea: bool,
    ci_image: bool,
    ci_image_registry_host: str | None,
    ci_image_registry_port: int | None,
    ci_image_registry_username: str | None,
    ci_image_registry_password: SecretLike | None,
    ci_image_namespace: str | None,
    ci_package_job_name_suffix: str | None,
    ci_package_trusted_publishing: bool,
    ci_pyright_prerelease: str | None,
    ci_pyright_resolution: str | None,
    ci_pytest_os: MaybeSequenceStr | None,
    ci_pytest_python_version: MaybeSequenceStr | None,
    ci_pytest_sops_age_key: SecretLike | None,
    ci_runs_on: MaybeSequenceStr | None,
    ci_tag_user_name: str | None,
    ci_tag_user_email: str | None,
    ci_tag_all: bool,
    ci_token_checkout: SecretLike | None,
    ci_token_github: SecretLike | None,
    description: str | None,
    direnv: bool,
    docker: bool,
    fish: bool,
    just: bool,
    lua: bool,
    prettier: bool,
    python: bool,
    python_index_name: str | None,
    python_index_url: str | None,
    python_index_username: str | None,
    python_index_password_read: SecretLike | None,
    python_index_password_write: SecretLike | None,
    python_package_name_external: str | None,
    python_package_name_internal: str | None,
    python_version: str | None,
    repo_name: str | None,
    shell: bool,
    toml: bool,
    xml: bool,
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
            ci_image=ci_image,
            ci_image_registry_host=ci_image_registry_host,
            ci_image_registry_port=ci_image_registry_port,
            ci_image_registry_username=ci_image_registry_username,
            ci_image_registry_password=ci_image_registry_password,
            ci_image_namespace=ci_image_namespace,
            ci_package_job_name_suffix=ci_package_job_name_suffix,
            ci_package_trusted_publishing=ci_package_trusted_publishing,
            ci_pyright_prerelease=ci_pyright_prerelease,
            ci_pyright_resolution=ci_pyright_resolution,
            ci_pytest_os=ci_pytest_os,
            ci_pytest_python_version=ci_pytest_python_version,
            ci_pytest_sops_age_key=ci_pytest_sops_age_key,
            ci_runs_on=ci_runs_on,
            ci_tag_user_name=ci_tag_user_name,
            ci_tag_user_email=ci_tag_user_email,
            ci_tag_all=ci_tag_all,
            ci_token_checkout=ci_token_checkout,
            ci_token_github=ci_token_github,
            description=description,
            direnv=direnv,
            docker=docker,
            fish=fish,
            just=just,
            lua=lua,
            prettier=prettier,
            python=python,
            python_index_name=python_index_name,
            python_index_url=python_index_url,
            python_index_username=python_index_username,
            python_index_password_read=python_index_password_read,
            python_index_password_write=python_index_password_write,
            python_package_name_external=python_package_name_external,
            python_package_name_internal=python_package_name_internal,
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
    ci_image: bool = False,
    ci_image_registry_host: str | None = None,
    ci_image_registry_port: int | None = None,
    ci_image_registry_username: str | None = None,
    ci_image_registry_password: SecretLike | None = None,
    ci_image_namespace: str | None = None,
    ci_package_job_name_suffix: str | None = None,
    ci_package_trusted_publishing: bool = False,
    ci_pyright_prerelease: str | None = None,
    ci_pyright_resolution: str | None = None,
    ci_pytest_os: MaybeSequenceStr | None = None,
    ci_pytest_python_version: MaybeSequenceStr | None = None,
    ci_pytest_sops_age_key: SecretLike | None = None,
    ci_runs_on: MaybeSequenceStr | None = None,
    ci_tag_user_name: str | None = None,
    ci_tag_user_email: str | None = None,
    ci_tag_all: bool = False,
    ci_token_checkout: SecretLike | None = None,
    ci_token_github: SecretLike | None = None,
    description: str | None = None,
    direnv: bool = False,
    docker: bool = False,
    fish: bool = False,
    just: bool = False,
    lua: bool = False,
    prettier: bool = False,
    python: bool = False,
    python_index_name: str | None = None,
    python_index_url: str | None = None,
    python_index_username: str | None = None,
    python_index_password_read: SecretLike | None = None,
    python_index_password_write: SecretLike | None = None,
    python_package_name_external: str | None = None,
    python_package_name_internal: str | None = None,
    python_version: str | None = None,
    repo_name: str | None = None,
    shell: bool = False,
    toml: bool = False,
    xml: bool = False,
) -> bool:
    funcs: list[Callable[[], bool]] = [
        partial(_add_check_versions_consistent, path=path),
        partial(_add_format_pre_commit_config, path=path),
        partial(_add_format_pytest, path=path),
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
    ci_github_or_gitea: dict[Literal["github", "gitea"], bool] = {}
    if ci_github:
        ci_github_or_gitea["github"] = False
    if ci_gitea:
        ci_github_or_gitea["gitea"] = True
    if len(ci_github_or_gitea) >= 1:
        funcs.append(partial(_add_update_ci_action_versions, path=path))
        funcs.append(partial(_add_update_ci_extensions, path=path))
    for gitea in ci_github_or_gitea.values():
        funcs.append(
            partial(
                _add_setup_ci_push,
                path=path,
                gitea=gitea,
                certificates=certificates,
                token_checkout=ci_token_checkout,
                token_github=ci_token_github,
                tag_user_name=ci_tag_user_name,
                tag_user_email=ci_tag_user_email,
                tag_major_minor=ci_tag_all,
                tag_major=ci_tag_all,
                tag_latest=ci_tag_all,
                package=python,
                package_job_name_suffix=ci_package_job_name_suffix,
                package_username=python_index_username,
                package_password=python_index_password_write,
                package_publish_url=python_index_url,
                package_trusted_publishing=ci_package_trusted_publishing,
                image=ci_image,
                image_runs_on=ci_runs_on,
                image_registry_host=ci_image_registry_host,
                image_registry_port=ci_image_registry_port,
                image_registry_username=ci_image_registry_username,
                image_registry_password=ci_image_registry_password,
                image_namespace=ci_image_namespace,
                image_uv_index=_to_read_url(python_index_url),
                image_uv_index_username=python_index_username,
                image_uv_index_password=python_index_password_read,
            )
        )
        funcs.append(
            partial(
                _add_setup_ci_pull_request,
                path=path,
                gitea=gitea,
                repo_name=repo_name,
                certificates=certificates,
                token_checkout=ci_token_checkout,
                token_github=ci_token_github,
                index=_to_read_url(python_index_url),
                index_username=python_index_username,
                index_password=python_index_password_read,
                python_version=python_version,
                pyright_resolution=ci_pyright_resolution,
                pyright_prerelease=ci_pyright_prerelease,
                pytest_runs_on=ci_runs_on,
                pytest_sops_age_key=ci_pytest_sops_age_key,
                pytest_os=ci_pytest_os,
                pytest_python_version=ci_pytest_python_version,
            )
        )
    if direnv and not python:
        funcs.append(partial(_add_setup_direnv, path=path, version=python_version))
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
                index=_to_read_url(python_index_url),
                index_username=python_index_username,
                index_password=python_index_password_read,
                native_tls=certificates,
            )
        )
        funcs.append(
            partial(
                _add_setup_bump_my_version,
                path=path,
                package_name=python_package_name_internal,
            )
        )
        funcs.append(partial(_add_setup_coverage, path=path))
        funcs.append(
            partial(
                _add_setup_direnv,
                path=path,
                python=True,
                index_name=python_index_name,
                index_username=python_index_username,
                index_password=python_index_password_read,
                native_tls=certificates,
                version=python_version,
            )
        )
        funcs.append(
            partial(
                _add_setup_pyproject,
                path=path,
                version=python_version,
                description=description,
                index_name=python_index_name,
                index_url=_to_read_url(python_index_url),
                name_external=python_package_name_external,
                name_internal=python_package_name_internal,
            )
        )
        funcs.append(partial(_add_setup_pyright, path=path, version=python_version))
        funcs.append(
            partial(
                _add_setup_pytest, path=path, package_name=python_package_name_internal
            )
        )
        funcs.append(partial(_add_setup_ruff, path=path, version=python_version))
        funcs.append(
            partial(
                _add_update_requirements,
                path=path,
                index=_to_read_url(python_index_url),
                index_username=python_index_username,
                index_password=python_index_password_read,
                native_tls=certificates,
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
        args=["--newline", "--write"],
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
        args=["--write"],
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


def _add_format_pytest(*, path: PathLike = PYTEST_TOML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "format-pytest",
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
    index: MaybeSequenceStr | None = None,
    index_username: str | None = None,
    index_password: SecretLike | None = None,
    native_tls: bool = False,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args(
        "--index",
        index,
        "--index-username",
        index_username,
        "--index-password",
        index_password,
        "--native-tls",
        native_tls,
        join=True,
    )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "run-uv-lock",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
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
        args=["--fix"],
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
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package_name: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--package-name", package_name, join=True)
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-bump-my-version",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_ci_pull_request(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    gitea: bool = False,
    repo_name: str | None = None,
    certificates: bool = False,
    token_checkout: SecretLike | None = None,
    token_github: SecretLike | None = None,
    index: MaybeSequenceStr | None = None,
    index_username: str | None = None,
    index_password: SecretLike | None = None,
    python_version: str | None = None,
    pyright_resolution: str | None = None,
    pyright_prerelease: str | None = None,
    pytest_runs_on: MaybeSequenceStr | None = None,
    pytest_sops_age_key: SecretLike | None = None,
    pytest_os: MaybeSequenceStr | None = None,
    pytest_python_version: MaybeSequenceStr | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args(
        "--gitea",
        gitea,
        "--repo-name",
        repo_name,
        "--certificates",
        certificates,
        "--token-checkout",
        token_checkout,
        "--token-github",
        token_github,
        "--index",
        index,
        "--index-username",
        index_username,
        "--index-password",
        index_password,
        "--python-version",
        python_version,
        "--pyright-resolution",
        pyright_resolution,
        "--pyright-prerelease",
        pyright_prerelease,
        "--pytest-runs-on",
        pytest_runs_on,
        "--pytest-sops-age-key",
        pytest_sops_age_key,
        "--pytest-os",
        pytest_os,
        "--pytest-python-version",
        pytest_python_version,
        join=True,
    )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ci-pull-request",
        path=path,
        modifications=modifications,
        args=args,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_ci_push(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    gitea: bool = False,
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
    args: list[str] = to_args(
        "--gitea",
        gitea,
        "--certificates",
        certificates,
        "--token-checkout",
        token_checkout,
        "--token-github",
        token_github,
        "--tag-user-name",
        tag_user_name,
        "--tag-user-email",
        tag_user_email,
        "--tag-major-minor",
        tag_major_minor,
        "--tag-major",
        tag_major,
        "--tag-latest",
        tag_latest,
        "--package",
        package,
        join=True,
    )
    if package:
        package_args: list[str] = to_args(
            "--package-job-name-suffix",
            package_job_name_suffix,
            "--package-username",
            package_username,
            "--package-password",
            package_password,
            "--package-publish-url",
            package_publish_url,
            "--package-trusted-publishing",
            package_trusted_publishing,
            join=True,
        )
        args.extend(package_args)
    args.extend(to_args("--image", image, join=True))
    if image:
        image_args: list[str] = to_args(
            "--image-runs-on",
            image_runs_on,
            "--image-registry-host",
            image_registry_host,
            "--image-registry-port",
            image_registry_port,
            "--image-registry-username",
            image_registry_username,
            "--image-registry-password",
            image_registry_password,
            "--image-namespace",
            image_namespace,
            "--image-uv-index",
            image_uv_index,
            "--image-uv-index-username",
            image_uv_index_username,
            "--image-uv-index-password",
            image_uv_index_password,
            join=True,
        )
        args.extend(image_args)
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ci-push",
        path=path,
        modifications=modifications,
        args=args,
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
    index_name: str | None = None,
    index_username: str | None = None,
    index_password: SecretLike | None = None,
    native_tls: bool = False,
    version: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args(
        "--python",
        python,
        "--index-name",
        index_name,
        "--index-username",
        index_username,
        "--index-password",
        index_password,
        "--native-tls",
        native_tls,
        "--version",
        version,
        join=True,
    )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-direnv",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_git(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, python: bool = False
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--python", python, join=True)
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-git",
        path=path,
        modifications=modifications,
        rev=True,
        args=args if len(args) >= 1 else None,
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
    version: str | None = None,
    description: str | None = None,
    index_name: str | None = None,
    index_url: str | None = None,
    name_external: str | None = None,
    name_internal: str | None = None,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args(
        "--version",
        version,
        "--description",
        description,
        "--index-name",
        index_name,
        "--index-url",
        index_url,
        "--name-external",
        name_external,
        "--name-internal",
        name_internal,
        join=True,
    )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pyproject",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_pyright(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, version: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--version", version, join=True)
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pyright",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_pytest(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package_name: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--package-name", package_name, join=True)
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-pytest",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
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
    args: list[str] = to_args(
        "--repo-name", repo_name, "--description", description, join=True
    )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-readme",
        path=path,
        modifications=modifications,
        rev=True,
        args=args,
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_ruff(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, version: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--version", version, join=True)
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "setup-ruff",
        path=path,
        modifications=modifications,
        rev=True,
        args=args if len(args) >= 1 else None,
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
        args=["--fix=lf"],
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
        args=["--autofix"],
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
        args=[
            "--option=indent_tables=true",
            "--option=indent_entries=true",
            "--option=reorder_keys=true",
        ],
        type_="formatter",
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
    index: MaybeSequenceStr | None = None,
    index_username: str | None = None,
    index_password: SecretLike | None = None,
    native_tls: bool = False,
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args(
        "--index",
        index,
        "--index-username",
        index_username,
        "--index-password",
        index_password,
        "--native-tls",
        native_tls,
        join=True,
    )
    _add_hook(
        DYCW_PRE_COMMIT_HOOKS_URL,
        "update-requirements",
        path=path,
        modifications=modifications,
        rev=True,
        args=args if len(args) >= 1 else None,
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
        args=["--eof-newline"],
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
    args: list[str] | None = None,
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
        if (args is not None) and (len(args) >= 1):
            args_list = get_set_list_strs(hook, "args")
            ensure_contains(args_list, *args)
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


@overload
def _to_read_url(url: None, /) -> None: ...
@overload
def _to_read_url(url: str, /) -> str: ...
def _to_read_url(url: str | None, /) -> str | None:
    if url is None:
        return None
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/simple", "", ""))


if __name__ == "__main__":
    _main()
