from __future__ import annotations

from pathlib import Path

from pytest import mark, param, raises

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

    def test_depth_2(self) -> None:
        result = merge_paths(PRE_COMMIT_CONFIG_YAML, target="foo/bar")
        expected = [Path("foo/bar")]
        assert result == expected

    def test_also_ok(self) -> None:
        result = merge_paths("path", target="target", also_ok="path")
        expected = [Path("target")]
        assert result == expected

    def test_error(self) -> None:
        with raises(ValueError, match=r"Invalid path; got 'path'"):
            _ = merge_paths("path", target="target")
