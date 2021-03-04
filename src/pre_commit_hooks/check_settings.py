import json
import sys
from argparse import ArgumentParser
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Sequence
from functools import lru_cache
from logging import INFO
from logging import basicConfig
from logging import info
from logging import warning
from pathlib import Path
from typing import Any
from typing import Iterable
from typing import Optional
from urllib.request import urlopen

import toml
import yaml
from git import Repo


basicConfig(level=INFO)


def check_black() -> None:
    config = read_pyproject_toml_tool()["black"]
    expected = {
        "line-length": 80,
        "skip-magic-trailing-comma": True,
        "target-version": ["py38"],
    }
    check_mapping_subset(config, expected)


def check_mapping_subset(
    config: Mapping[str, Any], expected: Mapping[str, Any]
) -> None:
    check_iterable_subset(config, expected)
    for i, con_i in config.items():
        exp_i = expected[i]
        try:
            iter(exp_i)
        except TypeError:
            if con_i != exp_i:
                raise ValueError(f"Field {i!r} should be: {exp_i}")
        else:
            check_iterable_subset(con_i, exp_i)


def check_flake8() -> None:
    path = get_repo_root().joinpath(".flake8")
    url = get_github_file(path.name)
    try:
        with open(path) as file:
            local = file.read()
    except FileNotFoundError:
        info(f"{path} not found; creating...")
        write_local(path, url)
    else:
        if local != read_remote(url):
            info(f"{path} is out-of-sync; updating...")
            write_local(path, url)


def check_hook_fields(
    repo_hooks: Mapping[str, Any],
    expected: Mapping[str, Iterable[str]],
    field: str,
) -> None:
    for hook, value in expected.items():
        current = repo_hooks[hook][field]
        check_iterable_subset(current, value)


def check_isort() -> None:
    config = read_pyproject_toml_tool()["isort"]
    expected = {
        "atomic": True,
        "float_to_top": True,
        "force_single_line": True,
        "line_length": 80,
        "lines_after_imports": 2,
        "profile": "black",
        "remove_redundant_aliases": True,
        "skip_gitignore": True,
        "src_paths": ["src"],
        "virtual_env": ".venv/bin/python",
    }
    check_mapping_subset(config, expected)


def check_key_equals(config: dict[str, Any], key: str, expected: Any) -> None:
    if config[key] != expected:
        raise ValueError(f"Incorrect {key!r}; expected {expected}")


def check_lists_equal(
    current: list[str], expected: list[str], desc: str
) -> None:
    if current != sorted(current):
        raise ValueError(f"{desc} actual is unsorted: {current}")
    if expected != sorted(expected):
        raise ValueError(f"{desc} expected is unsorted: {expected}")
    if extra := set(current) - set(expected):
        raise ValueError(f"{desc} has extra: {extra}")
    if missing := set(expected) - set(current):
        raise ValueError(f"{desc} is missing: {missing}")


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


def check_pyrightconfig() -> None:
    with open(get_repo_root().joinpath("pyrightconfig.json")) as file:
        config = json.load(file)
    expected = {
        "include": ["src"],
        "venvPath": ".venv",
        "executionEnvironments": [{"root": "src"}],
    }
    check_mapping_subset(config, expected)


def check_pytest() -> None:
    config = read_pyproject_toml_tool()["pytest"]["ini_options"]
    expected = {
        "addopts": [
            "-q",
            "-rsxX",
            "--color=yes",
            "--instafail",
            "--strict-markers",
        ],
        "minversion": 6.0,
        "looponfailroots": ["src"],
        "testpaths": ["src/tests"],
        "xfailstrict": True,
    }
    check_mapping_subset(config, expected)


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
        check_iterable_subset(repo_hooks, enabled_hooks)
    if hook_args is not None:
        check_hook_fields(repo_hooks, hook_args, "args")
    if hook_additional_dependencies is not None:
        check_hook_fields(
            repo_hooks, hook_additional_dependencies, "additional_dependencies"
        )
    if config_checker is not None:
        config_checker()


def check_iterable_subset(config: Iterable, expected: Iterable) -> None:
    set_con = set(config)
    set_exp = set(expected)
    if missing := set_exp - set_con:
        raise ValueError(f"Elements are missing: {missing}")
    if extra := set_con - set_exp:
        warning(f"Extra elements found: {extra}")


def get_flake8_extensions() -> list[str]:
    return read_remote(get_github_file("flake8-extensions")).splitlines()


def get_github_file(filename: str) -> str:
    return f"https://raw.githubusercontent.com/dycw/pre-commit-hooks/master/{filename}"


def get_pre_commit_repos() -> dict[str, dict[str, Any]]:
    with open(get_repo_root().joinpath(".pre-commit-config.yaml")) as file:
        config = yaml.safe_load(file)
    repo = "repo"
    return {
        mapping[repo]: {k: v for k, v in mapping.items() if k != repo}
        for mapping in config["repos"]
    }


def get_repo_hooks(repo: Mapping[str, Any]) -> dict[str, Any]:
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
    root = get_repo_root()
    args = parser.parse_args(argv)
    for filename in args.filenames:
        path = root.joinpath(filename)
        name = path.name
        if name == ".flake8":
            check_flake8()
        elif name == ".pre-commit-config.yaml":
            check_pre_commit_config_yaml()
        elif name == "pyproject.toml":
            config = read_pyproject_toml_tool()["poetry"]
            if (
                "pytest" in config["dependencies"]
                or "pytest" in config["dev-dependencies"]
            ):
                check_pytest()
        elif name == "pyrightconfig.json":
            check_pyrightconfig()
    return 0


def read_pyproject_toml_tool() -> Mapping[str, Any]:
    with open(get_repo_root().joinpath("pyproject.toml")) as file:
        return toml.load(file)["tool"]


@lru_cache
def read_remote(url: str) -> str:
    with urlopen(url) as file:  # noqa: S310
        return file.read().decode()


def write_local(path: Path, url: str) -> None:
    with open(path, mode="w") as file:
        file.write(read_remote(url))


if __name__ == "__main__":
    sys.exit(main())
