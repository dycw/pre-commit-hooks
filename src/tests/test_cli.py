from __future__ import annotations

from pytest import mark, param
from utilities.constants import HOUR
from utilities.pytest import throttle_test
from utilities.subprocess import run

from pre_commit_hooks.constants import (
    BUMPVERSION_TOML,
    PRE_COMMIT_CONFIG_YAML,
    PYPROJECT_TOML,
)


class TestCLI:
    @mark.parametrize(
        ("hook", "args"),
        [
            param("add-future-import-annotations", ["path.py"]),
            param("add-hooks", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("add-ruff-hooks", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("check-versions-consistent", [str(BUMPVERSION_TOML)]),
            param("format-requirements", [str(PYPROJECT_TOML)]),
            param("replace-sequence-str", ["path.py"]),
            param("run-prek-autoupdate", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("run-version-bump", [str(BUMPVERSION_TOML)]),
            param("update-requirements", [str(PYPROJECT_TOML)]),
        ],
    )
    @throttle_test(duration=HOUR)
    def test_main(self, *, hook: str, args: list[str]) -> None:
        run(hook, *args)
