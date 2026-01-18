from __future__ import annotations

from functools import partial
from pathlib import Path
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
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest

from pre_commit_hooks.utilities import run_all_maybe_raise, write_text

if TYPE_CHECKING:
    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p) for p in paths))


def _run(path: PathLike, /) -> bool:
    existing = Path(path).read_text()
    wrapper = MetadataWrapper(parse_module(existing))
    transformed = wrapper.module.visit(SequenceToListTransformer())
    new = transformed.code
    if existing == new:
        return True
    write_text(path, new)
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


if __name__ == "__main__":
    _main()
