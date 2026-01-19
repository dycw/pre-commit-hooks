from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.constants import HOUR
from utilities.pytest import throttle_test

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML
from pre_commit_hooks.hooks.add_hooks import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestAddHooks:
    @throttle_test(duration=HOUR)
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PRE_COMMIT_CONFIG_YAML
        for i in range(2):
            result = _run(path=path, max_workers=1)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
