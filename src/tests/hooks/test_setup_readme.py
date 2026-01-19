from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import README_MD
from pre_commit_hooks.hooks.setup_readme import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupReadme:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / README_MD
        for i in range(2):
            result = _run(path=path, repo_name="repo-name", description="description")
            expected = i >= 1
            assert result is expected
            assert path.is_file()
