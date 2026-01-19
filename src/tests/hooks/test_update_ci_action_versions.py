from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.hooks.update_ci_action_versions import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestUpdateCIExtensions:
    def test_main(self, *, tmp_path: Path) -> None:
        old = tmp_path / "foo.yml"
        old.touch()
        new = tmp_path / "foo.yaml"
        result = _run(old)
        assert result is False
        assert not old.exists()
        assert new.is_file()
