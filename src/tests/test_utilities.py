from __future__ import annotations

from typing import TYPE_CHECKING

from pytest import mark, param

if TYPE_CHECKING:
    from pathlib import Path


from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    GITHUB_PULL_REQUEST_YAML,
    PRE_COMMIT_CONFIG_YAML,
)
from pre_commit_hooks.utilities import merge_paths


class TestMergePaths:
    @mark.parametrize(
        ("paths", "target", "expected"),
        [
            param([PRE_COMMIT_CONFIG_YAML], BUMPVERSION_TOML, [BUMPVERSION_TOML]),
            param([BUMPVERSION_TOML], BUMPVERSION_TOML, [BUMPVERSION_TOML]),
            param(
                [PRE_COMMIT_CONFIG_YAML, BUMPVERSION_TOML],
                BUMPVERSION_TOML,
                [BUMPVERSION_TOML],
            ),
            param(
                [PRE_COMMIT_CONFIG_YAML],
                GITHUB_PULL_REQUEST_YAML,
                [GITHUB_PULL_REQUEST_YAML],
            ),
            param(
                [GITHUB_PULL_REQUEST_YAML],
                GITHUB_PULL_REQUEST_YAML,
                [GITHUB_PULL_REQUEST_YAML],
            ),
            param(
                [PRE_COMMIT_CONFIG_YAML, GITHUB_PULL_REQUEST_YAML],
                GITHUB_PULL_REQUEST_YAML,
                [GITHUB_PULL_REQUEST_YAML],
            ),
        ],
    )
    def test_main(
        self, *, paths: list[Path], target: Path, expected: list[Path]
    ) -> None:
        result = merge_paths(*paths, target=target)
        assert result == expected
