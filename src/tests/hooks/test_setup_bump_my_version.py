from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import BUMPVERSION_TOML
from pre_commit_hooks.hooks.setup_bump_my_version import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupBumpMyVersion:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / BUMPVERSION_TOML
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            assert path.is_file()
