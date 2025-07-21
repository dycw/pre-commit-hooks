from __future__ import annotations

from pathlib import Path

from pytest import fixture
from tomlkit import dumps

from pre_commit_hooks.format_requirements import _format


@fixture
def toml() -> Path:
    return Path(__file__).parent.joinpath("toml")


class TestFormatRequirements:
    def test_basic(self, *, toml: Path) -> None:
        root = toml.joinpath("basic")
        result = dumps(_format(root.joinpath("in.toml")))
        expected = root.joinpath("out.toml").read_text()
        assert result == expected
