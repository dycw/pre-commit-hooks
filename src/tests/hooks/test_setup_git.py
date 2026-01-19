from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITIGNORE
from pre_commit_hooks.hooks.setup_git import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupGitIgnore:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITIGNORE
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            assert path.is_file()
