from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.hooks.setup_pyproject import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupPyproject:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PYPROJECT_TOML
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
