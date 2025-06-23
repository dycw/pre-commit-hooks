from __future__ import annotations

import re
from re import MULTILINE
from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output
from sys import argv
from typing import TYPE_CHECKING

from click import argument, command
from libcst import CSTTransformer, Name, Subscript, parse_module
from libcst.matchers import Name as NameMatch
from libcst.matchers import matches
from libcst.metadata import MetadataWrapper
from loguru import logger
from utilities.click import FilePath
from utilities.version import Version, parse_version

from pre_commit_hooks.common import PYPROJECT_TOML

if TYPE_CHECKING:
    from pathlib import Path


@command()
@argument("paths", nargs=-1, type=FilePath)
def main(*, paths: tuple[Path, ...]) -> bool:
    """CLI for the `replace_sequence_str` hook."""
    results = list(map(_process, paths))
    return all(results)


def _process(path: Path, /) -> bool:
    existing = path.read_text()
    wrapper = MetadataWrapper(parse_module(existing))
    transformed = wrapper.module.visit(SequenceToListTransformer())
    new = transformed.code
    if existing == new:
        return True
    _ = path.write_text(new)
    return False


class SequenceToListTransformer(CSTTransformer):
    def leave_Subscript(
        self, original_node: Subscript, updated_node: Subscript
    ) -> Subscript:
        if matches(updated_node.value, NameMatch("Sequence")):
            return updated_node.with_changes(value=Name("list"))
        return updated_node


__all__ = ["main"]
