import sys
from argparse import ArgumentParser
from logging import basicConfig
from logging import INFO
from logging import info
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence
from urllib.request import urlopen

import toml
import yaml
from git import Repo

basicConfig(level=INFO)


class SettingsChecker:
    def __init__(
        self,
        repo_url: str,
        *,
        filename: Optional[str] = None,
        remote_url: Optional[str] = None,
    ) -> None:
        self.repo_url = repo_url
        self.filename = filename
        self.remote_url = remote_url

    def check(self) -> bool:
        repos = self.get_pre_commit_repos()
        try:
            repo = repos[self.repo_url]
        except KeyError:
            return True
        hooks = self.get_repo_hooks(repo)
        if not self.check_hooks(hooks):
            return False
        if self.filename is not None:
            local_path = self.get_repo_root().joinpath(self.filename)
            if not self.check_local(local_path):
                return False
        return True

    def check_hooks(self, hooks: Dict[str, Any]) -> bool:
        return True

    def check_local(self, local_path: Path) -> bool:
        if self.remote_url is not None and not self.check_local_vs_remote(
            local_path,
            self.remote_url,
        ):
            return False
        return True

    def check_local_vs_remote(self, local_path: Path, remote_url: str) -> bool:
        try:
            with open(local_path) as file:
                local = file.read()
        except FileNotFoundError:
            info(f"{local_path} not found; creating...")
            self.write_local(local_path, remote_url)
            return False
        if local == self.read_remote(remote_url):
            return True
        info(f"{local_path} is out-of-sync; updating...")
        self.write_local(local_path, remote_url)
        return False

    @classmethod
    def get_pre_commit_repos(cls) -> Dict[str, Dict[str, Any]]:
        with open(cls.get_repo_root().joinpath(".pre-commit-config.yaml")) as file:
            config = yaml.safe_load(file)
        repo = "repo"
        return {
            mapping[repo]: {k: v for k, v in mapping.items() if k != repo}
            for mapping in config["repos"]
        }

    @classmethod
    def get_repo_hooks(cls, repo: Dict[str, Any]) -> Dict[str, Any]:
        id_ = "id"
        return {
            mapping[id_]: {k: v for k, v in mapping.items() if k != id_}
            for mapping in repo["hooks"]
        }

    @staticmethod
    def get_repo_root() -> Path:
        return Path(Repo(".", search_parent_directories=True).working_tree_dir)

    def read_remote(self, url: str) -> str:
        with urlopen(url) as file:  # noqa: S310
            return file.read().decode()

    def write_local(self, local_path: Path, remote_url: str) -> None:
        with open(local_path, mode="w") as file:
            file.write(self.read_remote(remote_url))


class AutoFlakeChecker(SettingsChecker):
    def __init__(self) -> None:
        super().__init__(repo_url="https://github.com/myint/autoflake")

    def check_hooks(self, hooks: Dict[str, Any]) -> bool:
        current = hooks["autoflake"]["args"]
        expected = [
            "--in-place",
            "--remove-all-unused-imports",
            "--remove-duplicate-keys",
            "--remove-unused-variables",
        ]
        if current != expected:
            raise ValueError(f"Incorrect autoflake args:\n{current}\n{expected}")
        return True


class BlackChecker(SettingsChecker):
    def __init__(self) -> None:
        super().__init__(
            repo_url="https://github.com/psf/black",
            filename="pyproject.toml",
        )

    def check_local(self, local_path: Path) -> bool:
        pyproject = toml.load(local_path)
        black = pyproject["tool"]["black"]
        if (line_length := black["line-length"]) != 88:
            raise ValueError(f"Incorrect line length: {line_length}")
        if (target_version := black["target-version"]) != ["py38"]:
            raise ValueError(f"Incorrect target version: {target_version}")
        return True


class Flake8Checker(SettingsChecker):
    def __init__(self) -> None:
        super().__init__(
            repo_url="https://github.com/PyCQA/flake8",
            filename=".flake8",
            remote_url="https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/.flake8",
        )

    def check_hooks(self, hooks: Dict[str, Any]) -> bool:
        current = hooks["flake8"]["additional_dependencies"]
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
    def __init__(self) -> None:
        super().__init__(
            repo_url="https://github.com/PyCQA/pylint",
            filename=".pylintrc",
        )

    def read_remote(self, url: str) -> str:
        return """[MESSAGES CONTROL]
disable=
  arguments-differ,
  import-error,
  missing-class-docstring,
  missing-function-docstring,
  missing-module-docstring,
  no-self-use,
  too-many-arguments,
  unsubscriptable-object,
  unused-argument
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
    return (
        AutoFlakeChecker().check()
        and BlackChecker().check()
        and Flake8Checker().check()
        and PylintChecker().check()
    )


def read_file(path: Path) -> str:
    with open(path) as file:
        return file.read()


if __name__ == "__main__":
    sys.exit(main())
