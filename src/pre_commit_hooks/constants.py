from __future__ import annotations

from pathlib import Path

import utilities.click
from click import argument, option
from utilities.click import ListStrs
from utilities.constants import HOUR
from xdg_base_dirs import xdg_cache_home

BUILTIN = "builtin"
DOCKERFMT_URL = "https://github.com/reteps/dockerfmt"
DYCW_PRE_COMMIT_HOOKS_URL = "https://github.com/dycw/pre-commit-hooks"
LOCAL = "local"
RUFF_URL = "https://github.com/astral-sh/ruff-pre-commit"
SHELLCHECK_URL = "https://github.com/koalaman/shellcheck-precommit"
SHFMT_URL = "https://github.com/scop/pre-commit-shfmt"
STD_PRE_COMMIT_HOOKS_URL = "https://github.com/pre-commit/pre-commit-hooks"
STYLUA_URL = "https://github.com/johnnymorganz/stylua"
TAPLO_URL = "https://github.com/compwa/taplo-pre-commit"
UV_URL = "https://github.com/astral-sh/uv-pre-commit"
XMLFORMATTER_URL = "https://github.com/pamoller/xmlformatter"


BUMPVERSION_TOML = Path(".bumpversion.toml")
COVERAGERC_TOML = Path(".coveragerc.toml")
ENVRC = Path(".envrc")
GITEA = Path(".gitea")
GITHUB = Path(".github")
GITATTRIBUTES = Path(".gitattributes")
GITIGNORE = Path(".gitignore")
JUSTFILE = Path("justfile")
PRE_COMMIT_CONFIG_YAML = Path(".pre-commit-config.yaml")
PYPROJECT_TOML = Path("pyproject.toml")
PYRIGHTCONFIG_JSON = Path("pyrightconfig.json")
PYTEST_TOML = Path("pytest.toml")
README_MD = Path("README.md")
SSH = Path.home() / ".ssh"
RUFF_TOML = Path("ruff.toml")
UV_LOCK = Path("uv.lock")


GITHUB_WORKFLOWS, GITEA_WORKFLOWS = [g / "workflows" for g in [GITHUB, GITEA]]
GITHUB_PULL_REQUEST_YAML, GITEA_PULL_REQUEST_YAML = [
    w / "pull-request.yaml" for w in [GITHUB_WORKFLOWS, GITEA_WORKFLOWS]
]
GITHUB_PUSH_YAML, GITEA_PUSH_YAML = [
    w / "push.yaml" for w in [GITHUB_WORKFLOWS, GITEA_WORKFLOWS]
]


PATH_CACHE = xdg_cache_home() / "pre-commit-hooks"


PRE_COMMIT_PRIORITY = 10
EDITOR_PRIORITY = 20
FORMATTER_PRIORITY = 30
LINTER_PRIORITY = 40


PRE_COMMIT_CONFIG_REPO_KEYS = ["repo", "rev", "hooks"]
PRE_COMMIT_CONFIG_HOOK_KEYS = [
    "id",
    "alias",
    "name",
    "language_version",
    "files",
    "exclude",
    "types",
    "types_or",
    "exclude_types",
    "args",
    "stages",
    "additional_dependencies",
    "always_run",
    "verbose",
    "log_file",
    "priority",  # prek
]
PRE_COMMIT_HOOKS_HOOK_KEYS = [
    "id",
    "name",
    "entry",
    "language",
    "files",
    "exclude",
    "types",
    "types_or",
    "exclude_types",
    "always_run",
    "fail_fast",
    "verbose",
    "pass_filenames",
    "require_serial",
    "description",
    "language_version",
    "minimum_pre_commit_version",
    "args",
    "stages",
    "priority",  # prek
]


PYTHON_VERSION = "3.12"
MAX_PYTHON_VERSION = "3.14"


THROTTLE_DURATION = 12 * HOUR


certificates_option = option("--certificates", is_flag=True, default=False)
ci_pytest_os_option = option("--ci-pytest-os", type=ListStrs(), default=None)
ci_pytest_python_version_option = option(
    "--ci-pytest-python-version", type=ListStrs(), default=None
)
ci_pytest_runs_on_option = option("--ci-pytest-runs-on", type=ListStrs(), default=None)
ci_tag_all_option = option("--ci-tag-all", is_flag=True, default=False)
description_option = option("--description", type=str, default=None)
gitea_option = option("--gitea", is_flag=True, default=False)
paths_argument = argument("paths", nargs=-1, type=utilities.click.Path())
python_option = option("--python", is_flag=True, default=False)
python_package_name_external_option = option(
    "--python-package-name-external", type=str, default=None
)
python_package_name_internal_option = option(
    "--python-package-name-internal", type=str, default=None
)
python_uv_index_option = option("--python-uv-index", type=ListStrs(), default=None)
python_version_option = option("--python-version", type=str, default=None)
repo_name_option = option("--repo-name", type=str, default=None)
throttle_option = option("--throttle", is_flag=True, default=True)


__all__ = [
    "BUILTIN",
    "BUMPVERSION_TOML",
    "COVERAGERC_TOML",
    "DOCKERFMT_URL",
    "DYCW_PRE_COMMIT_HOOKS_URL",
    "EDITOR_PRIORITY",
    "ENVRC",
    "FORMATTER_PRIORITY",
    "GITATTRIBUTES",
    "GITEA",
    "GITEA_PULL_REQUEST_YAML",
    "GITEA_PUSH_YAML",
    "GITEA_WORKFLOWS",
    "GITHUB",
    "GITHUB_PULL_REQUEST_YAML",
    "GITHUB_PUSH_YAML",
    "GITHUB_WORKFLOWS",
    "GITIGNORE",
    "JUSTFILE",
    "LINTER_PRIORITY",
    "LOCAL",
    "MAX_PYTHON_VERSION",
    "PATH_CACHE",
    "PRE_COMMIT_CONFIG_HOOK_KEYS",
    "PRE_COMMIT_CONFIG_REPO_KEYS",
    "PRE_COMMIT_CONFIG_YAML",
    "PRE_COMMIT_PRIORITY",
    "PYPROJECT_TOML",
    "PYRIGHTCONFIG_JSON",
    "PYTEST_TOML",
    "PYTHON_VERSION",
    "README_MD",
    "RUFF_TOML",
    "RUFF_URL",
    "SHELLCHECK_URL",
    "SHFMT_URL",
    "SSH",
    "STD_PRE_COMMIT_HOOKS_URL",
    "STYLUA_URL",
    "TAPLO_URL",
    "THROTTLE_DURATION",
    "UV_LOCK",
    "UV_URL",
    "XMLFORMATTER_URL",
    "certificates_option",
    "ci_pytest_os_option",
    "ci_pytest_python_version_option",
    "ci_pytest_runs_on_option",
    "ci_tag_all_option",
    "description_option",
    "gitea_option",
    "paths_argument",
    "python_option",
    "python_package_name_external_option",
    "python_package_name_internal_option",
    "python_uv_index_option",
    "python_version_option",
    "repo_name_option",
    "throttle_option",
]
