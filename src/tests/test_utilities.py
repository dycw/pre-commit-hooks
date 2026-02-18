from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest import mark, param, raises

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML
from pre_commit_hooks.utilities import merge_paths

if TYPE_CHECKING:
    from utilities.types import MaybeSequence, PathLike


class TestMergePaths:
    @mark.parametrize(
        ("paths", "target", "also_ok", "expected"),
        [
            param([PRE_COMMIT_CONFIG_YAML], "target", None, ["target"]),
            param(["target"], "target", None, ["target"]),
            param([PRE_COMMIT_CONFIG_YAML, "target"], "target", None, ["target"]),
            param([PRE_COMMIT_CONFIG_YAML], "foo/bar", None, ["foo/bar"]),
            param(["foo/bar"], "foo/bar", None, ["foo/bar"]),
            param([PRE_COMMIT_CONFIG_YAML, "foo/bar"], "foo/bar", None, ["foo/bar"]),
            param(["path"], "target", "path", ["target"]),
            param(["target", "foo/bar"], "target", "foo/bar", ["target"]),
            param(["target", "foo/bar"], "foo/bar", "target", ["foo/bar"]),
        ],
    )
    def test_main(
        self,
        *,
        paths: list[Path],
        target: Path,
        also_ok: MaybeSequence[PathLike],
        expected: list[PathLike],
    ) -> None:
        result = merge_paths(*paths, target=target, also_ok=also_ok)
        exp_paths = list(map(Path, expected))
        assert result == exp_paths

    def test_error(self) -> None:
        with raises(ValueError, match=r"Invalid path; got 'path'"):
            _ = merge_paths("path", target="target")
