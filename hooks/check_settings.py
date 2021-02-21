import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from functools import lru_cache
from logging import basicConfig
from logging import INFO
from logging import info
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Tuple
from urllib.request import urlopen

import yaml
from git import Repo

basicConfig(level=INFO)


@dataclass(frozen=True)
class SettingsChecker:
    repo_url: str
    local_path_parts: Tuple[str, ...]
    remote_url: str

    def check(self) -> bool:
        repos = self.get_pre_commit_repos()
        try:
            repo = repos[self.repo_url]
        except KeyError:
            return True
        else:
            return self.check_hooks(repo) and self.check_local_vs_remote()

    def check_hooks(self, repo: Dict[str, Any]) -> bool:
        return bool(repo)

    def check_local_vs_remote(self) -> bool:
        try:
            local = self.read_local()
        except FileNotFoundError:
            info(f"{self.local_path} not found; creating...")
            self.write_local()
            return False
        if local == self.read_remote():
            return True
        info(f"{self.local_path} is out-of-sync; updating...")
        self.write_local()
        return False

    @classmethod
    @lru_cache
    def get_pre_commit_repos(cls) -> Dict[str, Dict[str, Any]]:
        with open(cls.get_repo_root().joinpath(".pre-commit-config.yaml")) as file:
            config = yaml.safe_load(file)
        repo = "repo"
        return {
            mapping[repo]: {k: v for k, v in mapping.items() if k != repo}
            for mapping in config["repos"]
        }

    @staticmethod
    @lru_cache
    def get_repo_root() -> Path:
        return Path(Repo(".", search_parent_directories=True).working_tree_dir)

    @property
    def local_path(self) -> Path:
        return self.get_repo_root().joinpath(*self.local_path_parts)

    @lru_cache
    def read_local(self) -> str:
        with open(self.local_path) as file:
            return file.read()

    @lru_cache
    def read_remote(self) -> str:
        with urlopen(self.remote_url) as file:  # noqa: S310
            return file.read().decode()

    def write_local(self) -> None:
        with open(self.local_path, mode="w") as file:
            file.write(self.read_remote())


class Flake8Checker(SettingsChecker):
    def check_hook(self, repo: Dict[str, Any]) -> bool:
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
        return True


class PylintChecker(SettingsChecker):
    @lru_cache
    def read_remote(self) -> str:
        return """[MESSAGES CONTROL]
disable=
  import-error,
  missing-class-docstring,
  missing-function-docstring,
  missing-module-docstring,
  no-self-use,
  too-many-arguments,
  unsubscriptable-object
"""


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
    flake8 = Flake8Checker(
        repo_url="https://github.com/PyCQA/flake8",
        local_path_parts=(".flake8",),
        remote_url="https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/.flake8",
    )
    pylint = PylintChecker(
        repo_url="https://github.com/PyCQA/pylint",
        local_path_parts=(".pylintrc",),
        remote_url="Nothing yet",
    )
    return flake8.check() and pylint.check()


def read_file(path: Path) -> str:
    with open(path) as file:
        return file.read()


def read_url(url: str) -> str:
    with urlopen(url) as file:  # noqa: S310
        return file.read().decode()


if __name__ == "__main__":
    sys.exit(main())
