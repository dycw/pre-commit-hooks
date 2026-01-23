from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, override

from click import command
from libcst import CSTTransformer, Name, Subscript
from libcst.matchers import Index as MIndex
from libcst.matchers import Name as MName
from libcst.matchers import Subscript as MSubscript
from libcst.matchers import SubscriptElement as MSubscriptElement
from libcst.matchers import matches
from libcst.metadata import MetadataWrapper
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest

from pre_commit_hooks.constants import paths_argument
from pre_commit_hooks.utilities import run_all_maybe_raise, yield_python_file

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, p) for p in paths))


def _run(path: PathLike, /) -> bool:
    modifications: set[Path] = set()
    with yield_python_file(path, modifications=modifications) as context:
        context.output = MetadataWrapper(context.input).module.visit(
            SequenceToListTransformer()
        )
    return len(modifications) == 0


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
