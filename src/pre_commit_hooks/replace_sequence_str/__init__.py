from __future__ import annotations

from typing import TYPE_CHECKING, override

import utilities.click
from click import argument, command
from libcst import CSTTransformer, Name, Subscript, parse_module
from libcst.matchers import Index as MIndex
from libcst.matchers import Name as MName
from libcst.matchers import Subscript as MSubscript
from libcst.matchers import SubscriptElement as MSubscriptElement
from libcst.matchers import matches
from libcst.metadata import MetadataWrapper

from pre_commit_hooks.common import run_all

if TYPE_CHECKING:
    from pathlib import Path


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
def main(*, paths: tuple[Path, ...]) -> bool:
    """CLI for the `replace-sequence-str` hook."""
    return run_all(map(_process, paths))


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
    @override
    def leave_Subscript(
        self, original_node: Subscript, updated_node: Subscript
    ) -> Subscript:
        _ = original_node
        if matches(
            updated_node,
            MSubscript(
                value=MName("Sequence"),
                slice=[MSubscriptElement(slice=MIndex(value=MName("str")))],
            ),
        ):
            return updated_node.with_changes(value=Name("list"))
        return updated_node


__all__ = ["main"]
