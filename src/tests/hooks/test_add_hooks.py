from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.text import strip_and_dedent

from pre_commit_hooks.hooks.add_hooks import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestAddHooks:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / "file.py"
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
