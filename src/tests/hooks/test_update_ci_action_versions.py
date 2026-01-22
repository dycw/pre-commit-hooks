from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import normalize_multi_line_str, read_text

from pre_commit_hooks.hooks.update_ci_action_versions import _run
from pre_commit_hooks.utilities import write_text_and_add_modification

if TYPE_CHECKING:
    from pathlib import Path


class TestUpdateCIActionVersions:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / "action.yaml"
        input_ = normalize_multi_line_str("""
            runs:
              steps:
                - uses: actions/checkout@v5
        """)
        write_text_and_add_modification(path, input_)
        expected = normalize_multi_line_str("""
            runs:
              steps:
                - uses: actions/checkout@v6
        """)
        for i in range(2):
            assert _run(path) is (i >= 1)
            assert read_text(path) == expected
