from __future__ import annotations

from pathlib import Path

from tomlkit import dumps

from pre_commit_hooks.format_requirements import _format_path


class TestFormatRequirements:
    def test_basic(self) -> None:
        root = Path(__file__).parent
        result = dumps(_format_path(root.joinpath("in.toml")))
        expected = root.joinpath("out.toml").read_text()
        assert result == expected
