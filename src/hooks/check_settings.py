import json
import sys
from argparse import ArgumentParser
from configparser import ConfigParser
from functools import lru_cache
from logging import basicConfig
from logging import INFO
from logging import info
from os import getenv
from pathlib import Path
from re import search
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import TextIO
from urllib.request import urlopen

import toml
import yaml
from git import Repo


basicConfig(level=INFO)


def check_coc_settings_json(path: Path) -> None:
    with open(get_repo_root().joinpath(path)) as file:
        coc_settings = json.load(file)
    python_path = Path(coc_settings["python.pythonPath"])
    check_env_path(python_path)


def check_env_path(path: Path) -> None:
    parts = list(path.parts)
    try:
        env = parts[parts.index("envs") + 1]
    except IndexError:
        raise ValueError(f"Unable to determine env from path: {path}")
    if env != get_environment_name():
        raise ValueError(f"Incorrect environment: {env}")
    if getenv("PRE_COMMIT_CI", "0") != "1" and not path.exists():
        raise FileNotFoundError(path)


def check_envrc() -> None:
    with open(get_repo_root().joinpath(".envrc")) as file:
        lines = file.readlines()
    expected = get_environment_name()
    for line in lines:
        if (match := search(r"^layout anaconda (.*)$", line)) and (
            current := match.group(1)
        ) != expected:
            raise ValueError(f"Incorrect environment: {current}")


def check_hook_fields(
    repo_hooks: Dict[str, Any],
    expected_mapping: Dict[str, List[str]],
    field: str,
) -> None:
    for hook_name, expected in expected_mapping.items():
        current = repo_hooks[hook_name][field]
        check_lists_equal(current, expected, f"{hook_name}.{field}")


def check_lists_equal(
    current: List[str], expected: List[str], desc: str
) -> None:
    if current != sorted(current):
        raise ValueError(f"{desc} actual is unsorted: {current}")
    if expected != sorted(expected):
        raise ValueError(f"{desc} expected is unsorted: {expected}")
    if extra := set(current) - set(expected):
        raise ValueError(f"{desc} has extra: {extra}")
    if missing := set(expected) - set(current):
        raise ValueError(f"{desc} is missing: {missing}")


def check_local_vs_remote(filename: str) -> None:
    local_path = get_repo_root().joinpath(filename)
    remote_url = get_github_file(filename)
    try:
        with open(local_path) as file:
            local = file.read()
    except FileNotFoundError:
        info(f"{local_path} not found; creating...")
        write_local(local_path, remote_url)
    else:
        if local != read_remote(remote_url):
            info(f"{local_path} is out-of-sync; updating...")
            write_local(local_path, remote_url)


def check_pre_commit_config_yaml(path: Path) -> None:
    repos = get_pre_commit_repos(path)
    check_repo(
        repos,
        "https://github.com/asottile/add-trailing-comma",
        hook_args={"add-trailing-comma": ["--py36-plus"]},
    )
    check_repo(
        repos,
        "https://github.com/asottile/pyupgrade",
        hook_args={"pyupgrade": ["--py38-plus"]},
    )
    check_repo(
        repos,
        "https://github.com/asottile/reorder_python_imports",
        hook_args={"reorder-python-imports": ["--py37-plus"]},
    )
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
        repos,
        "https://github.com/psf/black",
        config_filename="pyproject.toml",
        config_checker=check_pyproject_toml,
    )
    check_repo(
        repos,
        "https://github.com/PyCQA/flake8",
        hook_additional_dependencies={"flake8": get_flake8_extensions()},
        config_filename=".flake8",
        config_remote=True,
    )
    check_repo(
        repos,
        "https://github.com/pre-commit/mirrors-mypy",
        config_filename="mypy.ini",
        config_remote=True,
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
        "https://github.com/asottile/yesqa",
        hook_additional_dependencies={"yesqa": get_flake8_extensions()},
    )


def check_pyproject_toml(file: TextIO) -> None:
    pyproject = toml.load(file)
    black = pyproject["tool"]["black"]
    if (line_length := black["line-length"]) != 80:
        raise ValueError(f"Incorrect line length: {line_length}")
    if not (skip_magic_trailing_comma := black["skip-magic-trailing-comma"]):
        raise ValueError(
            f"Incorrect skip magic trailing comma: {skip_magic_trailing_comma}"
        )
    if (target_version := black["target-version"]) != ["py38"]:
        raise ValueError(f"Incorrect target version: {target_version}")


def check_pyrightconfig_json(path: Path) -> None:
    with open(get_repo_root().joinpath(path)) as file:
        pyrightconfig = json.load(file)
    venv_path = pyrightconfig["venvPath"]
    venv = pyrightconfig["venv"]
    check_env_path(Path(venv_path, venv))


def check_pytest_ini(path: Path) -> None:
    parser = ConfigParser()
    with open(get_repo_root().joinpath(path)) as file:
        parser.read_file(file)
    pytest = parser["pytest"]
    addopts = pytest["addopts"].strip("\n").splitlines()
    if addopts != sorted(addopts):
        raise ValueError(f"addopts is unsorted: {addopts}")
    for opt in ["-q", "-rsxX", "--color=yes"]:
        if opt not in addopts:
            raise ValueError(f"addopts missing: {opt}")
    looponfailroots = pytest["looponfailroots"].strip("\n").splitlines()
    for root in ["tests"]:
        if root not in looponfailroots:
            raise ValueError(f"looponfailroots missing: {root}")
    if (minversion := pytest["minversion"]) != "6.0":
        raise ValueError(f"Incorrect min version: {minversion}")


def check_repo(
    repos: Dict[str, Dict[str, Any]],
    repo_url: str,
    *,
    enabled_hooks: Optional[List[str]] = None,
    hook_args: Optional[Dict[str, List[str]]] = None,
    hook_additional_dependencies: Optional[Dict[str, List[str]]] = None,
    config_filename: Optional[str] = None,
    config_checker: Optional[Callable[[TextIO], None]] = None,
    config_remote: bool = False,
) -> None:
    try:
        repo = repos[repo_url]
    except KeyError:
        return

    repo_hooks = get_repo_hooks(repo)
    if enabled_hooks is not None:
        check_lists_equal(
            current=list(repo_hooks), expected=enabled_hooks, desc="hook set"
        )
    if hook_args is not None:
        check_hook_fields(repo_hooks, hook_args, "args")
    if hook_additional_dependencies is not None:
        check_hook_fields(
            repo_hooks, hook_additional_dependencies, "additional_dependencies"
        )

    config_filename_absent = ValueError('"config_filename" is absent')
    if (config_checker is not None) and not config_remote:
        if config_filename is None:
            raise config_filename_absent
        with open(get_repo_root().joinpath(config_filename)) as file:
            config_checker(file)
    elif (config_checker is None) and config_remote:
        if config_filename is None:
            raise config_filename_absent
        check_local_vs_remote(config_filename)
    elif (config_checker is not None) and config_remote:
        raise ValueError(
            '"config_checker" and "config_remote" are mutually exclusive'
        )


def get_environment_name() -> str:
    with open(get_repo_root().joinpath("environment.yml")) as file:
        environment = yaml.safe_load(file)
    return environment["name"]


def get_flake8_extensions() -> List[str]:
    return read_remote(get_github_file("flake8-extensions")).splitlines()


def get_github_file(filename: str) -> str:
    return f"https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/{filename}"


def get_pre_commit_repos(path: Path) -> Dict[str, Dict[str, Any]]:
    with open(get_repo_root().joinpath(path)) as file:
        config = yaml.safe_load(file)
    repo = "repo"
    return {
        mapping[repo]: {k: v for k, v in mapping.items() if k != repo}
        for mapping in config["repos"]
    }


def get_repo_hooks(repo: Dict[str, Any]) -> Dict[str, Any]:
    id_ = "id"
    return {
        mapping[id_]: {k: v for k, v in mapping.items() if k != id_}
        for mapping in repo["hooks"]
    }


def get_repo_root() -> Path:
    path = Repo(".", search_parent_directories=True).working_tree_dir
    if not isinstance(path, str):
        raise ValueError(f"Invalid path: {path}")
    return Path(path)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    for filename in args.filenames:
        path = Path(filename)
        name = path.name
        if name == ".pre-commit-config.yaml":
            check_pre_commit_config_yaml(path)
        elif ".vim" in path.parts and name == "coc-settings.json":
            check_coc_settings_json(path)
        elif name == "pyrightconfig.json":
            check_pyrightconfig_json(path)
        elif name == "pytest.ini":
            check_pytest_ini(path)
    return 0


@lru_cache
def read_remote(url: str) -> str:
    with urlopen(url) as file:  # noqa: S310
        return file.read().decode()


def read_file(path: Path) -> str:
    with open(path) as file:
        return file.read()


def write_local(local_path: Path, url: str) -> None:
    with open(local_path, mode="w") as file:
        file.write(read_remote(url))


if __name__ == "__main__":
    sys.exit(main())
