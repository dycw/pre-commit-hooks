import sys
from argparse import ArgumentParser
from functools import lru_cache
from logging import basicConfig
from logging import INFO
from logging import info
from pathlib import Path
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


def check_repo(
    repo_url: str,
    *,
    hook_args: Optional[Dict[str, List[str]]] = None,
    hook_additional_dependencies: Optional[Dict[str, List[str]]] = None,
    config_filename: Optional[str] = None,
    config_checker: Optional[Callable[[TextIO], None]] = None,
    config_remote: Optional[str] = None,
) -> None:
    repos = get_pre_commit_repos()
    try:
        repo = repos[repo_url]
    except KeyError:
        return

    hooks = get_repo_hooks(repo)
    if hook_args is not None:
        check_hook_fields(hooks, hook_args, "args")
    if hook_additional_dependencies is not None:
        check_hook_fields(
            hooks,
            hook_additional_dependencies,
            "additional_dependencies",
        )
    if config_checker is not None and config_remote is None:
        if config_filename is None:
            raise CONFIG_FILENAME_IS_ABSENT
        with open(get_repo_root().joinpath(config_filename)) as file:
            config_checker(file)
    elif config_remote is not None and config_checker is None:
        if config_filename is None:
            raise CONFIG_FILENAME_IS_ABSENT
        check_local_vs_remote(config_filename, config_remote)
    elif config_checker is not None and config_remote is not None:
        raise ValueError('"config_checker" and "config_remote" are mutually exclusive')


def check_hook_fields(
    hooks: Dict[str, Any],
    expected: Dict[str, List[str]],
    field: str,
) -> None:
    for key, value in expected.items():
        current = hooks[key][field]
        if current != sorted(current):
            raise ValueError(f"{key!r} {field} are unsorted: {current}")
        if value != sorted(value):
            raise ValueError(f"{key!r} expected {field} are unsorted: {value}")
        if extra := set(current) - set(value):
            raise ValueError(f"{key!r} has extra {field}: {extra}")
        if missing := set(value) - set(current):
            raise ValueError(f"{key!r} has missing {field}: {missing}")


CONFIG_FILENAME_IS_ABSENT = ValueError('"config_filename" is absent')


def check_local_vs_remote(filename: str, url: str) -> None:
    local_path = get_repo_root().joinpath(filename)
    try:
        with open(local_path) as file:
            local = file.read()
    except FileNotFoundError:
        info(f"{local_path} not found; creating...")
        write_local(local_path, url)
    else:
        if local != read_remote(url):
            info(f"{local_path} is out-of-sync; updating...")
            write_local(local_path, url)


def check_pylintrc(file: TextIO) -> None:
    actual = file.read()
    expected = """[MESSAGES CONTROL]
disable=
  import-error,
  missing-class-docstring,
  missing-function-docstring,
  missing-module-docstring,
  no-self-use,
  too-many-arguments,
  unsubscriptable-object,
  unused-argument
"""
    if actual != expected:
        raise ValueError(f"Actual=\n{actual}\n\nexpected=\n{expected}")


def check_pre_commit_config() -> None:
    check_repo(
        repo_url="https://github.com/asottile/add-trailing-comma",
        hook_args={"add-trailing-comma": ["--py36-plus"]},
    )
    check_repo(
        repo_url="https://github.com/asottile/pyupgrade",
        hook_args={"add-trailing-comma": ["--py38-plus"]},
    )
    check_repo(
        repo_url="https://github.com/myint/autoflake",
        hook_args={
            "autoflake": [
                "--in-place",
                "--remove-all-unused-imports",
                "--remove-duplicate-keys",
                "--remove-unused-variables",
            ],
        },
    )
    check_repo(
        repo_url="https://github.com/psf/black",
        config_filename="pyproject.toml",
        config_checker=check_pyproject_toml_black,
    )
    check_repo(
        repo_url="https://github.com/PyCQA/flake8",
        hook_additional_dependencies={
            "flake8": [
                "dlint",
                "flake8-absolute-import",
                "flake8-annotations",
                "flake8-bandit",
                "flake8-bugbear",
                "flake8-builtins",
                "flake8-commas",
                "flake8-comprehensions",
                "flake8-debugger",
                "flake8-eradicate",
                "flake8-executable",
                "flake8-fine-pytest",
                "flake8-fixme",
                "flake8-future-import",
                "flake8-implicit-str-concat",
                "flake8-mutable",
                "flake8-print",
                "flake8-pytest-style",
                "flake8-simplify",
                "flake8-string-format",
                "flake8-todo",
                "flake8-typing-imports",
                "flake8-unused-arguments",
                "pep8-naming",
            ],
        },
        config_filename=".flake8",
        config_remote="https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/.flake8",
    )
    check_repo(
        repo_url="https://github.com/PyCQA/pylint",
        config_filename=".pylintrc",
        config_checker=check_pylintrc,
    )


def check_pyproject_toml_black(file: TextIO) -> None:
    pyproject = toml.load(file)
    black = pyproject["tool"]["black"]
    if (line_length := black["line-length"]) != 88:
        raise ValueError(f"Incorrect line length: {line_length}")
    if (target_version := black["target-version"]) != ["py38"]:
        raise ValueError(f"Incorrect target version: {target_version}")


def get_pre_commit_repos() -> Dict[str, Dict[str, Any]]:
    with open(get_repo_root().joinpath(".pre-commit-config.yaml")) as file:
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
    return Path(Repo(".", search_parent_directories=True).working_tree_dir)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    for filename in args.filenames:
        check_file(filename)
    info("ok...")
    return 0


def check_file(filename: str) -> None:
    if filename != ".pre-commit-config.yaml":
        return
    check_repo(
        repo_url="https://github.com/myint/autoflake",
        hook_args={
            "autoflake": [
                "--in-place",
                "--remove-all-unused-imports",
                "--remove-duplicate-keys",
                "--remove-unused-variables",
            ],
        },
    )
    check_repo(
        repo_url="https://github.com/psf/black",
        config_filename="pyproject.toml",
        config_checker=check_pyproject_toml_black,
    )
    check_repo(
        repo_url="https://github.com/PyCQA/flake8",
        hook_additional_dependencies={
            "flake8": [
                "dlint",
                "flake8-absolute-import",
                "flake8-annotations",
                "flake8-bandit",
                "flake8-bugbear",
                "flake8-builtins",
                "flake8-commas",
                "flake8-comprehensions",
                "flake8-debugger",
                "flake8-eradicate",
                "flake8-executable",
                "flake8-fine-pytest",
                "flake8-fixme",
                "flake8-future-import",
                "flake8-implicit-str-concat",
                "flake8-mutable",
                "flake8-print",
                "flake8-pytest-style",
                "flake8-simplify",
                "flake8-string-format",
                "flake8-todo",
                "flake8-typing-imports",
                "flake8-unused-arguments",
                "pep8-naming",
            ],
        },
        config_filename=".flake8",
        config_remote="https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/.flake8",
    )
    check_repo(
        repo_url="https://github.com/PyCQA/pylint",
        config_filename=".pylintrc",
        config_checker=check_pylintrc,
    )


def check_pyproject_toml_black(file: TextIO) -> None:
    pyproject = toml.load(file)
    black = pyproject["tool"]["black"]
    if (line_length := black["line-length"]) != 88:
        raise ValueError(f"Incorrect line length: {line_length}")
    if (target_version := black["target-version"]) != ["py38"]:
        raise ValueError(f"Incorrect target version: {target_version}")


def get_pre_commit_repos() -> Dict[str, Dict[str, Any]]:
    with open(get_repo_root().joinpath(".pre-commit-config.yaml")) as file:
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
    return Path(Repo(".", search_parent_directories=True).working_tree_dir)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    for filename in args.filenames:
        if filename == ".pre-commit-config.yaml":
            check_pre_commit_config()
    info("ok...")
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
