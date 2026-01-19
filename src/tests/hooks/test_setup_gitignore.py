from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITIGNORE, PRE_COMMIT_CONFIG_YAML
from pre_commit_hooks.hooks.setup_gitignore import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupGitIgnore:
    def test_main(self, *, tmp_path: Path) -> None:
        for i in range(2):
            result = _run(path=tmp_path / PRE_COMMIT_CONFIG_YAML)
            exp_result = i >= 1
            assert result is exp_result
            assert (tmp_path / GITIGNORE).is_file()
