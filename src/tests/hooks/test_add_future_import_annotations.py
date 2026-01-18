from __future__ import annotations

from typing import TYPE_CHECKING

from pytest import fixture
from utilities.text import strip_and_dedent

from pre_commit_hooks.hooks.add_future_import_annotations import _run

if TYPE_CHECKING:
    from pathlib import Path


@fixture
def output() -> str:
    return strip_and_dedent(
        """
from __future__ import annotations
""",
        trailing=True,
    )


class TestFormatPath:
    def test_main(self, *, tmp_path: Path, output: str) -> None:
        path = tmp_path / "file.py"
        path.touch()
        for i in range(2):
            result = _run(path, throttle=False)
            expected = i >= 1
            assert result is expected
            contents = path.read_text()
            assert contents == output
