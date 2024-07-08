from __future__ import annotations

from subprocess import CalledProcessError, check_call
from typing import cast

from click import command
from loguru import logger
from tomlkit import dumps, table
from tomlkit.container import Container

from pre_commit_hooks.common import PYPROJECT_TOML, PyProject, read_pyproject


@command()
def main() -> bool:
    """CLI for the `run-ruff-format` hook."""
    return _process()


def _process() -> bool:
    curr = read_pyproject()
    new = _get_modified_pyproject()
    result1 = _run_ruff_format(new)
    result2 = _run_ruff_format(curr)
    _write_pyproject(curr)
    return result1 and result2


def _get_modified_pyproject() -> PyProject:
    pyproject = read_pyproject()
    doc = pyproject.doc
    try:
        tool = cast(Container, doc["tool"])
    except KeyError:
        tool = table()
    try:
        ruff = cast(Container, tool["ruff"])
    except KeyError:
        ruff = table()
    ruff["line-length"] = 320
    try:
        format_ = cast(Container, ruff["format"])
    except KeyError:
        format_ = table()
    format_["skip-magic-trailing-comma"] = True
    try:
        lint = cast(Container, ruff["lint"])
    except KeyError:
        lint = table()
    try:
        isort = cast(Container, lint["isort"])
    except KeyError:
        isort = table()
    isort["split-on-trailing-comma"] = False
    doc["tool"] = tool
    tool["ruff"] = ruff
    ruff["format"] = format_
    ruff["lint"] = lint
    lint["isort"] = isort
    return PyProject(contents=dumps(doc), doc=doc)


def _run_ruff_format(pyproject: PyProject, /) -> bool:
    _write_pyproject(pyproject)
    cmd = ["ruff", "format", "."]
    try:
        code = check_call(cmd)
    except CalledProcessError:
        logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
        return False
    return code == 0


def _write_pyproject(pyproject: PyProject, /) -> None:
    with PYPROJECT_TOML.open(mode="w") as fh:
        _ = fh.write(pyproject.contents)
