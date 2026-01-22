from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import normalize_multi_line_str

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
        exp_output = normalize_multi_line_str("""
            runs:
              steps:
                - uses: actions/checkout@v6
        """)
        for i in range(2):
            result = _run(path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
