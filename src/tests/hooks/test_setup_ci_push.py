from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITHUB_PUSH_YAML
from pre_commit_hooks.hooks.setup_ci_push import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupCIPush:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITHUB_PUSH_YAML
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
