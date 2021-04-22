import json
import sys
from argparse import ArgumentParser
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from configparser import ConfigParser
from contextlib import suppress
from functools import lru_cache
from itertools import chain
from pathlib import Path
from re import search
from typing import Any
from typing import Iterable
from typing import Optional
from urllib.request import urlopen

import toml
import yaml
from frozendict import frozendict
from git import Repo
from loguru import logger

from dycw_pre_commit_hooks.utilities import split_gitignore_lines


def check_black() -> None:
    config = read_pyproject_toml_tool()["black"]
    expected = {
        "line-length": 80,
        "skip-magic-trailing-comma": True,
        "target-version": ["py38"],
    }
    check_value_or_values(config, expected)


def check_value_or_values(actual: Any, expected: Any) -> None:
    if is_iterable(actual) and is_iterable(expected):
        if isinstance(actual, Mapping) and isinstance(expected, Mapping):
            for key, value in expected.items():
                try:
                    check_value_or_values(actual[key], value)
                except KeyError:
                    raise ValueError(f"Missing {key=}")
            desc = "key"
        else:
            for value in expected:
                if freeze(value) not in freeze(actual):
                    raise ValueError(f"Missing {value=}")
            desc = "value"
        for extra in set(freeze(actual)) - set(freeze(expected)):
            logger.warning(f"\nExtra {desc} found: {extra}")
    else:
        if actual != expected:
            raise ValueError(f"Differing values: {actual=} != {expected=}")


def check_flake8() -> None:
    parser = ConfigParser()
    with open(get_repo_root().joinpath(".flake8")) as file:
        parser.read_file(file)
    config = {
        k: v.split(",") if k == "ignore" else v
        for k, v in parser["flake8"].items()
    }
    expected = {
        "ignore": [
            # flake8-annotations
            "ANN101",  # Missing type annotation for self in method
            "ANN102",  # Missing type annotation for cls in classmethod
            # flake8-bandit
            "S310",  # Audit url open for permitted schemes
            "S322",  # The input method in Python 2 will read from...
            "S403",  # Consider possible security implications... [pickle]
            "S404",  # Consider possible security implications... [subprocess]
            "S603",  # subprocess call - check for execution of untrusted input
            "S607",  # Starting a process with a partial executable path
            # flake8-builtins
            "A003",  # class attribute ... is shadowing a python builtin
            # flake8-bugbear
            "B008",  # Do not perform function calls in argument defaults
            # flake8-fine-pytest
            "FP003",  # File ... is in the wrong directory
            "FP004",  # ... has too complex signature
            "FP005",  # ... has too many assert statements
            "FP009",  # Duplicate name test case
            # flake8-pytest-style
            "PT013",  # found incorrect import of pytest, use simple ...
            "PT019",  # fixture ... without value is injected as ...
            # flake8-simplify
            "SIM106",  # Handle error-cases first
            # flake8-string-format
            "P101",  # format string does contain unindexed parameters
            # flake8-unused-arguments
            "U101",  # unused argument [underscore]
            # pep8-naming
            "N802",  # function name '...' should be lowercase
            "N803",  # argument name '...' should be lowercase
            "N806",  # variable '...' in function should be lowercase
            # pycodestyle
            "E203",  # whitespace before ':'             | black
            "W503",  # line break before binary operator | black
        ],
        "max-line-length": "88",
        "min-python-version": "3.9",
        "per-file-ignores": "*/tests/*.py:S101",
        "show-source": "True",
        "suppress-dummy-args": "True",
        "unused-arguments-ignore-abstract-functions": "True",
    }
    check_value_or_values(config, expected)

    config = read_pyproject_toml_tool()["poetry"]["dev-dependencies"]
    flake8s = {item for item in config if search("(^flake8|pep8-naming)", item)}
    check_value_or_values(flake8s, get_flake8_extensions())


def check_github_action(
    filename: str, mandatory: list[str], optional: list[str]
) -> None:
    full_filename = f".github/workflows/{filename}"
    with open(get_repo_root().joinpath(full_filename)) as file:
        local = yaml.safe_load(file)
    remote = yaml.safe_load(read_remote(full_filename))
    check_value_or_values(local["name"], remote["name"])
    check_value_or_values(local[True], remote[True])  # the "on" clause
    loc_jobs = local["jobs"]
    rem_jobs = remote["jobs"]
    check_jobs = list(
        chain(mandatory, (job for job in optional if job in loc_jobs))
    )
    for job in check_jobs:
        loc_job = loc_jobs[job]
        if job == "pytest":
            step = next(
                step
                for step in loc_job["steps"]
                if "actions/setup-python@v2" in step.values()
            )
            with suppress(KeyError):
                del step["with"]
        check_value_or_values(loc_job, rem_jobs[job])


def check_gitignore() -> None:
    with open(get_repo_root().joinpath(".gitignore")) as file:
        lines = file.read().strip("\n").splitlines()
    for group in split_gitignore_lines(lines):
        if group != (s := sorted(group)):
            raise ValueError(f"Unsorted group should be: {s}")


def check_hook_fields(
    repo_hooks: Mapping[str, Any],
    expected: Mapping[str, Iterable[str]],
    field: str,
) -> None:
    for hook, value in expected.items():
        current = repo_hooks[hook][field]
        check_value_or_values(current, value)


def check_isort() -> None:
    config = read_pyproject_toml_tool()["isort"]
    expected = {
        "atomic": True,
        "force_single_line": True,
        "line_length": 80,
        "lines_after_imports": 2,
        "profile": "black",
        "remove_redundant_aliases": True,
        "skip_gitignore": True,
        "src_paths": ["src"],
        "virtual_env": ".venv/bin/python",
    }
    check_value_or_values(config, expected)


def check_pre_commit_config_yaml() -> None:
    repos = get_pre_commit_repos()
    check_repo(
        repos,
        "https://github.com/myint/autoflake",
        hook_args={
            "autoflake": [
                "--in-place",
                "--remove-all-unused-imports",
                "--remove-duplicate-keys",
                "--remove-unused-variables",
            ]
        },
    )
    check_repo(
        repos, "https://github.com/psf/black", config_checker=check_black
    )
    check_repo(
        repos,
        "https://github.com/PyCQA/flake8",
        hook_additional_dependencies={"flake8": get_flake8_extensions()},
        config_checker=check_flake8,
    )
    check_repo(
        repos,
        "https://github.com/pre-commit/mirrors-isort",
        config_checker=check_isort,
    )
    check_repo(
        repos,
        "https://github.com/pre-commit/pre-commit",
        enabled_hooks=["validate_manifest"],
    )
    check_repo(
        repos,
        "https://github.com/jumanjihouse/pre-commit-hooks",
        enabled_hooks=[
            "script-must-have-extension",
            "script-must-not-have-extension",
        ],
    )
    check_repo(
        repos,
        "https://github.com/pre-commit/pre-commit-hooks",
        enabled_hooks=[
            "check-case-conflict",
            "check-executables-have-shebangs",
            "check-merge-conflict",
            "check-symlinks",
            "check-vcs-permalinks",
            "destroyed-symlinks",
            "detect-private-key",
            "end-of-file-fixer",
            "fix-byte-order-marker",
            "mixed-line-ending",
            "no-commit-to-branch",
            "trailing-whitespace",
        ],
        hook_args={"mixed-line-ending": ["--fix=lf"]},
    )
    check_repo(
        repos,
        "https://github.com/a-ibs/pre-commit-mirrors-elm-format",
        hook_args={"elmformat": ["--yes"]},
    )
    check_repo(
        repos,
        "https://github.com/asottile/pyupgrade",
        hook_args={"pyupgrade": ["--py39-plus"]},
    )
    check_repo(
        repos,
        "https://github.com/asottile/yesqa",
        hook_additional_dependencies={"yesqa": get_flake8_extensions()},
    )
    check_repo(repos, "meta", enabled_hooks=["check-useless-excludes"])


def check_pyrightconfig() -> None:
    with open(get_repo_root().joinpath("pyrightconfig.json")) as file:
        config = json.load(file)
    expected = {
        "include": ["src"],
        "venvPath": ".venv",
        "executionEnvironments": [{"root": "src"}],
    }
    check_value_or_values(config, expected)


def check_pytest() -> None:
    config = read_pyproject_toml_tool()["pytest"]["ini_options"]
    expected = {
        "addopts": ["-q", "-rsxX", "--color=yes", "--strict-markers"],
        "minversion": 6.0,
        "xfail_strict": True,
        "log_level": "WARNING",
        "log_cli_date_format": "%Y-%m-%d %H:%M:%S",
        "log_cli_format": (
            "[%(asctime)s.%(msecs)03d] [%(levelno)d] [%(name)s:%(funcName)s] "
            "[%(process)d]\n%(msg)s"
        ),
        "log_cli_level": "WARNING",
    }
    if get_repo_root().joinpath("src").exists():
        expected["testpaths"] = ["src/tests"]
        if is_dependency("pytest-xdist"):
            expected["looponfailroots"] = ["src"]
    if is_dependency("pytest-instafail"):
        expected["addopts"].append("--instafail")  # type: ignore
    check_value_or_values(config, expected)


def check_repo(
    repos: Mapping[str, Mapping[str, Any]],
    repo_url: str,
    *,
    enabled_hooks: Optional[Iterable[str]] = None,
    hook_args: Optional[Mapping[str, Iterable[str]]] = None,
    hook_additional_dependencies: Optional[Mapping[str, Iterable[str]]] = None,
    config_checker: Optional[Callable] = None,
    # Callable is bugged - https://bit.ly/3bapBly
) -> None:
    try:
        repo = repos[repo_url]
    except KeyError:
        return

    repo_hooks = get_repo_hooks(repo)
    if enabled_hooks is not None:
        check_value_or_values(repo_hooks, enabled_hooks)
    if hook_args is not None:
        check_hook_fields(repo_hooks, hook_args, "args")
    if hook_additional_dependencies is not None:
        check_hook_fields(
            repo_hooks, hook_additional_dependencies, "additional_dependencies"
        )
    if config_checker is not None:
        config_checker()


def freeze(x: Any) -> Any:
    if isinstance(x, Mapping):
        return frozendict({k: freeze(v) for k, v in x.items()})
    elif is_iterable(x):
        return frozenset(map(freeze, x))
    else:
        return x


def get_flake8_extensions() -> set[str]:
    return {
        "flake8-absolute-import",
        "flake8-annotations",
        "flake8-bandit",
        "flake8-bugbear",
        "flake8-builtins",
        "flake8-comprehensions",
        "flake8-debugger",
        "flake8-eradicate",
        "flake8-executable",
        "flake8-fine-pytest",
        "flake8-implicit-str-concat",
        "flake8-mutable",
        "flake8-print",
        "flake8-pytest-style",
        "flake8-simplify",
        "flake8-string-format",
        "flake8-unused-arguments",
        "pep8-naming",
    }


def get_pre_commit_repos() -> Mapping[str, Mapping[str, Any]]:
    with open(get_repo_root().joinpath(".pre-commit-config.yaml")) as file:
        config = yaml.safe_load(file)
    repo = "repo"
    return {
        mapping[repo]: {k: v for k, v in mapping.items() if k != repo}
        for mapping in config["repos"]
    }


def get_repo_hooks(repo: Mapping[str, Any]) -> Mapping[str, Any]:
    id_ = "id"
    return {
        mapping[id_]: {k: v for k, v in mapping.items() if k != id_}
        for mapping in repo["hooks"]
    }


def get_repo_root() -> Path:
    path = Repo(".", search_parent_directories=True).working_tree_dir
    if isinstance(path, str):
        return Path(path)
    raise ValueError(f"Invalid {path=}")


def is_dependency(package: str) -> bool:
    config = read_pyproject_toml_tool()["poetry"]
    return (
        package in config["dependencies"]
        or package in config["dev-dependencies"]
    )


def is_iterable(x: Any) -> bool:
    return isinstance(x, Iterable) and not isinstance(x, str)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    root = get_repo_root()
    args = parser.parse_args(argv)
    for filename in args.filenames:
        path = root.joinpath(filename)
        name = path.name
        if name == ".flake8":
            check_flake8()
        elif name == ".gitignore":
            check_gitignore()
        elif name == ".pre-commit-config.yaml":
            check_pre_commit_config_yaml()
        elif name == "pull-request.yml":
            check_github_action(name, ["pre-commit"], ["pytest"])
        elif name == "push.yml":
            check_github_action(name, ["tag"], ["publish"])
        elif name == "pyproject.toml" and is_dependency("pytest"):
            check_pytest()
        elif name == "pyrightconfig.json":
            check_pyrightconfig()
    return 0


def read_pyproject_toml_tool() -> Mapping[str, Any]:
    with open(get_repo_root().joinpath("pyproject.toml")) as file:
        return toml.load(file)["tool"]


@lru_cache
def read_remote(filename: str) -> str:
    with urlopen(
        "https://raw.githubusercontent.com/dycw/pre-commit-hooks/"
        f"master/{filename}"
    ) as file:
        return file.read().decode()


if __name__ == "__main__":
    sys.exit(main())
