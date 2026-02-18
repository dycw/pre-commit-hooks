from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITHUB_PULL_REQUEST_YAML
from pre_commit_hooks.hooks.setup_ci_pull_request import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupCIPullRequest:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITHUB_PULL_REQUEST_YAML
        for i in range(2):
            result = _run(path=path, set_up=True)
            expected = i >= 1
            assert result is expected
            assert path.is_file()

    def test_no_set_up(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITHUB_PULL_REQUEST_YAML
        assert _run(path=path)
        assert not path.exists()
