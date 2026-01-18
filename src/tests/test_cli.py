from __future__ import annotations

from typing import TYPE_CHECKING

from hypothesis import HealthCheck, Phase, given, reproduce_failure, settings
from pytest import RaisesGroup, approx, fixture, mark, param, raises, skip
from utilities.contextvars import set_global_breakpoint
from utilities.subprocess import run

from pre_commit_hooks.constants import BUMPVERSION_TOML, PRE_COMMIT_CONFIG_YAML

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture
    from pytest_lazy_fixtures import lf
    from pytest_regressions.dataframe_regression import DataFrameRegressionFixture


class TestCLI:
    @mark.parametrize(
        ("hook", "args"),
        [
            param("add-hooks", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("add-ruff-hooks", [str(PRE_COMMIT_CONFIG_YAML)]),
            param("check-versions-consistent", [str(BUMPVERSION_TOML)]),
            param("run-version-bump", [str(BUMPVERSION_TOML)]),
        ],
    )
    def test_main(self, *, hook: str, args: list[str]) -> None:
        run(hook, *args)
