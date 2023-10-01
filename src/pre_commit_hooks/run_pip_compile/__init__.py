import datetime as dt
from collections.abc import Iterable
from collections.abc import Iterator
from pathlib import Path
from re import MULTILINE
from re import sub
from subprocess import CalledProcessError
from subprocess import check_call
from tempfile import TemporaryDirectory
from textwrap import indent
from typing import cast

import click
from click import argument
from click import command
from loguru import logger
from tomlkit import dumps
from tomlkit import parse
from tomlkit.container import Container
from utilities.git import get_repo_root

from pre_commit_hooks.common import PYPROJECT_TOML


@command()
@argument(
    "paths",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
)
def main(paths: tuple[Path, ...]) -> bool:
    """CLI for the `run-pip-compile` hook."""
    results = list(_yield_outcomes(*paths))  # run all
    return all(results)


def _yield_outcomes(*paths: Path) -> Iterator[bool]:
    for path in paths:
        if (filename := path.name) == "requirements.in":
            yield _process_dependencies(filename)
        elif filename == "requirements-dev.in":
            yield _process_dev_dependencies(filename)


# ---- dependencies -----------------------------------------------------------


def _process_dependencies(req_in: Path | str, /) -> bool:
    curr = _get_curr_pyproject_deps(PYPROJECT_TOML)
    latest = _run_pip_compile(req_in)
    if curr == latest:
        return True
    _write_pyproject_deps(PYPROJECT_TOML, latest)
    return False


def _get_curr_pyproject_deps(path: Path, /) -> set[str]:
    try:
        with path.open(mode="r") as fh:
            contents = fh.read()
    except FileNotFoundError:
        logger.exception("pyproject.toml not found")
        raise
    doc = parse(contents)
    try:
        project = cast(Container, doc["project"])
    except KeyError:
        logger.exception('pyproject.toml has no "project" section')
        raise
    try:
        dependencies = project["dependencies"]
    except KeyError:
        logger.exception('pyproject.toml has no "project.dependencies" section')
        raise
    return set(cast(Iterable[str], dependencies))


def _run_pip_compile(filename: Path | str, /) -> set[str]:
    with TemporaryDirectory() as temp:
        temp_file = Path(temp, "temp.txt")
        cmd = [
            "pip-compile",
            "--allow-unsafe",
            "--no-annotate",
            "--no-emit-index-url",
            "--no-emit-trusted-host",
            "--no-header",
            f"--output-file={temp_file.as_posix()}",
            "--quiet",
            "--upgrade",
            Path(filename).as_posix(),
        ]
        try:
            _ = check_call(cmd)  # noqa: S603
        except CalledProcessError:
            logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
            raise
        with temp_file.open(mode="r") as fh:
            lines = fh.readlines()
    lines = (line.strip("\n") for line in lines)
    return set(filter(_is_requirements_dep, lines))


def _is_requirements_dep(line: str, /) -> bool:
    return len(line) >= 1 and not line.startswith("#")


def _write_pyproject_deps(path: Path, deps: Iterable[str], /) -> None:
    with path.open(mode="r") as fh:
        contents = fh.read()
    doc = parse(contents)
    project = cast(Container, doc["project"])
    now = dt.datetime.now(tz=dt.UTC)
    dummy = f"PIP_COMPILE_{now:%4Y%m%dT%H%M%S}"
    project["dependencies"] = dummy
    contents_with_dummy = dumps(doc)
    repl = _get_replacement_text(deps)
    new_contents = sub(f'"{dummy}"', repl, contents_with_dummy, flags=MULTILINE)
    _ = parse(new_contents)  # check
    with path.open(mode="w") as fh:
        _ = fh.write(new_contents)


def _get_replacement_text(deps: Iterable[str], /) -> str:
    quoted = (f'"{dep}",' for dep in sorted(deps))
    indented = indent("\n".join(quoted), "  ")
    return f"[\n{indented}\n]"


# ---- dev dependencies -------------------------------------------------------


def _process_dev_dependencies(req_in: Path | str, /) -> bool:
    req_txt = get_repo_root().joinpath("requirements.txt")
    try:
        curr = _get_curr_requirements_deps(req_txt)
    except FileNotFoundError:
        latest = _run_pip_compile(req_in)
        _write_latest_dev_deps(req_txt, latest)
        return False
    latest = _run_pip_compile(req_in)
    if curr == latest:
        return True
    _write_latest_dev_deps(req_txt, latest)
    return False


def _get_curr_requirements_deps(path: Path, /) -> set[str]:
    with path.open(mode="r") as fh:
        lines = fh.readlines()
    return set(filter(_is_requirements_dep, lines))


def _write_latest_dev_deps(req_txt: Path, deps: Iterable[str], /) -> None:
    contents = "\n".join(sorted(deps)) + "\n"
    with req_txt.open(mode="w") as fh:
        _ = fh.write(contents)
