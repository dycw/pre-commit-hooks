from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.text import strip_and_dedent

from pre_commit_hooks.hooks.add_future_import_annotations import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestFormatPath:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / "file.py"
        path.touch()
        exp_output = strip_and_dedent(
            """
            from __future__ import annotations
            """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path, throttle=False)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
