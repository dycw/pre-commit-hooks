from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import BUMPVERSION_TOML, GITATTRIBUTES, GITIGNORE
from pre_commit_hooks.hooks.setup_git import _run_gitattributes, _run_gitignore

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupGit:
    def test_gitattributes(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITATTRIBUTES
        bumpversion = tmp_path / BUMPVERSION_TOML
        for i in range(2):
            result = _run_gitattributes(path=path, bumpversion=bumpversion)
            expected = i >= 1
            assert result is expected
            assert path.is_file()

    def test_gitignore(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITIGNORE
        for i in range(2):
            result = _run_gitignore(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
