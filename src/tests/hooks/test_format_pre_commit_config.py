from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.text import strip_and_dedent

from pre_commit_hooks.hooks.format_pre_commit_config import _run
from pre_commit_hooks.utilities import write_text

if TYPE_CHECKING:
    from pathlib import Path


class TestRun:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / "file.yaml"
        input_ = strip_and_dedent(
            """
            repos:
              - hooks:
                  - args:
                      - --arg1
                      - --arg2
                    id: repo2-hook2
                    priority: priority22
                  - args:
                      - --arg1
                      - --arg2
                    id: repo2-hook1
                    priority: priority21
                repo: repo2
                rev: rev2
              - hooks:
                  - args:
                      - --arg1
                      - --arg2
                    id: repo1-hook2
                    priority: priority12
                  - args:
                      - --arg1
                      - --arg2
                    id: repo1-hook1
                    priority: priority11
                repo: repo1
                rev: rev1
            """,
            trailing=True,
        )
        write_text(path, input_)
        exp_output = strip_and_dedent(
            """
            repos:
            - hooks:
              - id: repo1-hook1
                args:
                - --arg1
                - --arg2
                priority: priority11
              - id: repo1-hook2
                args:
                - --arg1
                - --arg2
                priority: priority12
              repo: repo1
              rev: rev1
            - hooks:
              - id: repo2-hook1
                args:
                - --arg1
                - --arg2
                priority: priority21
              - id: repo2-hook2
                args:
                - --arg1
                - --arg2
                priority: priority22
              repo: repo2
              rev: rev2
              """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
