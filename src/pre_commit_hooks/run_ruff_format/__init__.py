from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from subprocess import CalledProcessError, check_call
from typing import cast

from click import command
from loguru import logger
from tomlkit import TOMLDocument, dumps, table
from tomlkit.container import Container

from pre_commit_hooks.common import PYPROJECT_TOML, read_pyproject


@command()
def main() -> bool:
    """CLI for the `run-ruff-format` hook."""
    return _process()


def _process() -> bool:
    with _yield_modified_pyproject():
        result1 = _run_ruff_format()
    result2 = _run_ruff_format()
    return result1 and result2


@contextmanager
def _yield_modified_pyproject() -> Iterator[None]:
    curr = read_pyproject()
    new = _get_modified_pyproject()
    with PYPROJECT_TOML.open(mode="w") as fh:
        _ = fh.write(dumps(new))
    yield
    with PYPROJECT_TOML.open(mode="w") as fh:
        _ = fh.write(curr.contents)


def _get_modified_pyproject() -> TOMLDocument:
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
    return doc


def _run_ruff_format() -> bool:
    cmd = ["ruff", "format", "."]
    try:
        code = check_call(cmd)  # noqa: S603
    except CalledProcessError:
        logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
        raise
    return code == 0
