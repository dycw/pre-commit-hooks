from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import BUMPVERSION_TOML, GITATTRIBUTES, GITIGNORE
from pre_commit_hooks.hooks.setup_git import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupGit:
    def test_main(self, *, tmp_path: Path) -> None:
        attributes = tmp_path / GITATTRIBUTES
        bumpversion = tmp_path / BUMPVERSION_TOML
        ignore = tmp_path / GITIGNORE
        for i in range(2):
            result = _run(attributes=attributes, bumpversion=bumpversion, ignore=ignore)
            expected = i >= 1
            assert result is expected
            assert ignore.is_file()
