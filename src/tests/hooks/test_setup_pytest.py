from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import PYTEST_TOML
from pre_commit_hooks.hooks.setup_pytest import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestSetupPytest:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PYTEST_TOML
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
