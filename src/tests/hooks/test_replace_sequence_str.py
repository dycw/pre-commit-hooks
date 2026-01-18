from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.text import strip_and_dedent

from pre_commit_hooks.hooks.replace_sequence_str import _run
from pre_commit_hooks.utilities import write_text

if TYPE_CHECKING:
    from pathlib import Path


class TestRun:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / "file.py"
        input_ = strip_and_dedent(
            """
            from collections.abc import Sequence

            x: Sequence[str]
            """,
            trailing=True,
        )
        write_text(path, input_)
        exp_output = strip_and_dedent(
            """
            from collections.abc import Sequence

            x: list[str]
            """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
