from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import normalize_multi_line_str, read_text

from pre_commit_hooks.hooks.add_future_import_annotations import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestFormatPath:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / "file.py"
        expected = normalize_multi_line_str("""
            from __future__ import annotations
        """)
        for i in range(2):
            assert _run(path, throttle=False) is (i >= 1)
            assert read_text(path) == expected
