from __future__ import annotations

from typing import TYPE_CHECKING

from pytest import fixture
from utilities.text import strip_and_dedent

from pre_commit_hooks.hooks.replace_sequence_str import _run
from pre_commit_hooks.utilities import write_text

if TYPE_CHECKING:
    from pathlib import Path


@fixture
def input_() -> str:
    return strip_and_dedent(
        """
from collections.abc import Sequence

x: Sequence[str]
""",
        trailing=True,
    )


@fixture
def output() -> str:
    return strip_and_dedent(
        """
from collections.abc import Sequence

x: list[str]
""",
        trailing=True,
    )


class TestRun:
    def test_main(self, *, tmp_path: Path, input_: str, output: str) -> None:
        path = tmp_path / "file.py"
        write_text(path, input_)
        for i in range(2):
            result = _run(path)
            expected = i >= 1
            assert result is expected
            contents = path.read_text()
            assert contents == output
