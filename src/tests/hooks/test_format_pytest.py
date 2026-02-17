from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.core import normalize_multi_line_str, read_text

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML
from pre_commit_hooks.hooks.format_pytest import _run
from pre_commit_hooks.utilities import write_text_and_add_modification

if TYPE_CHECKING:
    from pathlib import Path


class TestRun:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PRE_COMMIT_CONFIG_YAML
        input_ = normalize_multi_line_str("""
            [pytest]
              d = [
                "--arg2",
                "--arg1",
              ]
              c = "c"
              b = [
                "--arg2",
                "--arg1",
              ]
              a = "a"
            """)
        write_text_and_add_modification(path, input_)
        expected = normalize_multi_line_str("""
            [pytest]
              a = "a"
              b = ["--arg1", "--arg2"]
              c = "c"
              d = ["--arg1", "--arg2"]
        """)
        for i in range(2):
            assert _run(path=path) is (i >= 1)
            assert read_text(path) == expected
