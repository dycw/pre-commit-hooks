from __future__ import annotations

from pathlib import Path

import utilities.click
from click import argument, option
from utilities.constants import HOUR
from xdg_base_dirs import xdg_cache_home

BUILTIN = "builtin"
DOCKERFMT_URL = "https://github.com/reteps/dockerfmt"
DYCW_PRE_COMMIT_HOOKS_URL = "https://github.com/dycw/pre-commit-hooks"
RUFF_URL = "https://github.com/astral-sh/ruff-pre-commit"
SHELLCHECK_URL = "https://github.com/koalaman/shellcheck-precommit"
SHFMT_URL = "https://github.com/scop/pre-commit-shfmt"
STD_PRE_COMMIT_HOOKS_URL = "https://github.com/pre-commit/pre-commit-hooks"
TAPLO_URL = "https://github.com/compwa/taplo-pre-commit"
UV_URL = "https://github.com/astral-sh/uv-pre-commit"


BUMPVERSION_TOML = Path(".bumpversion.toml")
COVERAGERC_TOML = Path(".coveragerc.toml")
ENVRC = Path(".envrc")
GITEA = Path(".gitea")
GITHUB = Path(".github")
GITIGNORE = Path(".gitignore")
PRE_COMMIT_CONFIG_YAML = Path(".pre-commit-config.yaml")
PYPROJECT_TOML = Path("pyproject.toml")
PYRIGHTCONFIG_JSON = Path("pyrightconfig.json")
PYTEST_TOML = Path("pytest.toml")
README_MD = Path("README.md")
SSH = Path.home() / ".ssh"
RUFF_TOML = Path("ruff.toml")


DEFAULT_PYTHON_VERSION = "3.12"
MAX_PYTHON_VERSION = "3.14"


FORMATTER_PRIORITY = 10
LINTER_PRIORITY = 20


GITHUB_WORKFLOWS, GITEA_WORKFLOWS = [g / "workflows" for g in [GITHUB, GITEA]]
GITHUB_PULL_REQUEST_YAML, GITEA_PULL_REQUEST_YAML = [
    w / "pull-request.yaml" for w in [GITHUB_WORKFLOWS, GITEA_WORKFLOWS]
]
GITHUB_PUSH_YAML, GITEA_PUSH_YAML = [
    w / "push.yaml" for w in [GITHUB_WORKFLOWS, GITEA_WORKFLOWS]
]


PATH_CACHE = xdg_cache_home() / "pre-commit-hooks"


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


THROTTLE_DURATION = 12 * HOUR


paths_argument = argument("paths", nargs=-1, type=utilities.click.Path())
python_package_name_option = option("--python-package-name", type=str, default=None)
python_version_option = option(
    "--python-version", type=str, default=DEFAULT_PYTHON_VERSION
)
throttle_option = option("--throttle", is_flag=True, default=True)


__all__ = [
    "BUILTIN",
    "BUMPVERSION_TOML",
    "COVERAGERC_TOML",
    "DEFAULT_PYTHON_VERSION",
    "DOCKERFMT_URL",
    "DYCW_PRE_COMMIT_HOOKS_URL",
    "ENVRC",
    "FORMATTER_PRIORITY",
    "GITEA",
    "GITEA_PULL_REQUEST_YAML",
    "GITEA_PUSH_YAML",
    "GITEA_WORKFLOWS",
    "GITHUB",
    "GITHUB_PULL_REQUEST_YAML",
    "GITHUB_PUSH_YAML",
    "GITHUB_WORKFLOWS",
    "GITIGNORE",
    "LINTER_PRIORITY",
    "MAX_PYTHON_VERSION",
    "PATH_CACHE",
    "PRE_COMMIT_CONFIG_HOOK_KEYS",
    "PRE_COMMIT_CONFIG_REPO_KEYS",
    "PRE_COMMIT_CONFIG_YAML",
    "PYPROJECT_TOML",
    "PYRIGHTCONFIG_JSON",
    "PYTEST_TOML",
    "README_MD",
    "RUFF_TOML",
    "RUFF_URL",
    "SHELLCHECK_URL",
    "SHFMT_URL",
    "SSH",
    "STD_PRE_COMMIT_HOOKS_URL",
    "TAPLO_URL",
    "THROTTLE_DURATION",
    "UV_URL",
    "paths_argument",
    "python_package_name_option",
    "python_version_option",
    "throttle_option",
]
