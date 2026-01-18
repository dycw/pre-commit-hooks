from __future__ import annotations

from pytest import mark, param
from utilities.subprocess import run

from pre_commit_hooks.constants import BUMPVERSION_TOML, PRE_COMMIT_CONFIG_YAML


class TestCLI:
    @mark.parametrize(
        ("hook", "args"),
        [
            param("add-hooks", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("add-ruff-hooks", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("check-versions-consistent", [str(BUMPVERSION_TOML)]),
            param("replace-sequence-str", ["path.py"]),
            param("run-version-bump", [str(BUMPVERSION_TOML)]),
        ],
    )
    def test_main(self, *, hook: str, args: list[str]) -> None:
        run(hook, *args)
