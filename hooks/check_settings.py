from argparse import ArgumentParser
from functools import lru_cache
from logging import basicConfig
from logging import INFO
from logging import info
from pathlib import Path
from sys import exit
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from urllib.request import urlopen

import yaml
from git import Repo

basicConfig(level=INFO)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    out = 0 if all(check_file(filename) for filename in args.filenames) else 1
    info(f"final out {out}")
    return out


def check_file(filename: str) -> bool:
    if filename != ".pre-commit-config.yaml":
        return True
    root = Path(Repo(".", search_parent_directories=True).working_tree_dir)
    repos = _get_pre_commit_repos(filename)
    return check_flake8(root, repos) and check_pylint(root, repos)


def _get_pre_commit_repos(filename: str) -> Dict[str, Any]:
    with open(filename) as file:
        config = yaml.safe_load(file)
    repo = "repo"
    return {
        mapping[repo]: {k: v for k, v in mapping.items() if k != repo}
        for mapping in config["repos"]
    }


def check_flake8(root: Path, repos: Dict[str, Dict[str, Any]]) -> bool:
    try:
        repo = repos["https://gitlab.com/pycqa/flake8"]
    except KeyError:
        return True
    current = repo["hooks"][0]["additional_dependencies"]
    expected = [
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
    ]
    if expected != sorted(expected):
        raise ValueError("Expected dependencies must be sorted")
    if extra := set(current) - set(expected):
        raise ValueError(f"flake8 has extra dependencies: {extra}")
    if missing := set(expected) - set(current):
        raise ValueError(f"flake8 has missing dependencies: {missing}")
    flake8 = root.joinpath(".flake8")

    def write_flake8() -> bool:
        with open(flake8, mode="w") as file:
            file.write(get_remote())
        return False

    @lru_cache
    def get_remote() -> str:
        return read_url(
            "https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/.flake8",
        )

    try:
        local = read_file(flake8)
    except FileNotFoundError:
        info(".flake8 not found; creating...")
        return write_flake8()
    if local == get_remote():
        return True
    else:
        info(".flake8 is out-of-sync; updating...")
        return write_flake8()


def check_pylint(root: Path, repos: Dict[str, Dict[str, Any]]) -> bool:
    try:
        repo = repos["https://github.com/pycqa/pylint"]
    except KeyError:
        return True
    pylint = root.joinpath(".pylintrc")
    raise NotImplementedError(repo, pylint)


def read_file(path: Path) -> str:
    with open(path) as file:
        return file.read()


def read_url(url: str) -> str:
    with urlopen(url) as file:  # noqa: S310
        return file.read().decode()


if __name__ == "__main__":
    exit(main())
