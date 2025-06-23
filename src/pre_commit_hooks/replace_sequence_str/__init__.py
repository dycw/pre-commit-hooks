from __future__ import annotations

import re
from pathlib import Path
from re import MULTILINE
from subprocess import PIPE, STDOUT, CalledProcessError, check_call, check_output
from sys import argv

from click import command
from libcst import CSTTransformer, Name, Subscript, parse_module
from libcst.matchers import Name as NameMatch
from libcst.matchers import matches
from libcst.metadata import MetadataWrapper
from loguru import logger
from utilities.version import Version, parse_version

from pre_commit_hooks.common import PYPROJECT_TOML


@command()
def main() -> bool:
    """CLI for the `replace_sequence_str` hook."""
    paths = list(map(Path, argv[1:]))
    paths = [p for p in paths if p.suffix == ".py"]
    results = list(map(_process, paths))
    return all(results)


def _process(path: Path, /) -> bool:
    return True
    try:
        original_code = path.read_text(encoding="utf-8")
        wrapper = MetadataWrapper(parse_module(original_code))
        transformed = wrapper.module.visit(SequenceToListTransformer())
        new_code = transformed.code

        if original_code == new_code:
            return True  # No changes made

        path.write_text(new_code, encoding="utf-8")
        return False  # Rewritten
    except Exception as e:
        print(f"[!] Error processing {path}: {e}", file=sys.stderr)
        return False


class SequenceToListTransformer(CSTTransformer):
    def leave_Subscript(
        self, original_node: Subscript, updated_node: Subscript
    ) -> Subscript:
        if matches(updated_node.value, NameMatch("Sequence")):
            return updated_node.with_changes(value=Name("list"))
        return updated_node


__all__ = ["main"]
