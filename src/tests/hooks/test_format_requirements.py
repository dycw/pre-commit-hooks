from __future__ import annotations

from typing import TYPE_CHECKING

from pytest import mark, param
from utilities.core import normalize_multi_line_str

from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.hooks.format_requirements import _run
from pre_commit_hooks.utilities import write_text_and_add_modification

if TYPE_CHECKING:
    from pathlib import Path


class TestRun:
    @mark.parametrize(
        ("input_", "output", "expected"),
        [
            param("package", "package", True),
            param("package>=1.2.3", "package>=1.2.3", True),
            param("package  >=  1.2.3", "package>=1.2.3", False),
            param("package<1.2", "package<1.2", True),
            param("package  <  1.2", "package<1.2", False),
            param("package>=1.2.3,<1.3", "package>=1.2.3, <1.3", False),
            param("package  >=  1.2.3  ,  <  1.3", "package>=1.2.3, <1.3", False),
            param("package<1.3,>=1.2.3", "package>=1.2.3, <1.3", False),
            param("package[extra]", "package[extra]", True),
            param("package[extra]>=1.2.3", "package[extra]>=1.2.3", True),
            param("package[extra]  >=  1.2.3", "package[extra]>=1.2.3", False),
        ],
    )
    def test_main(
        self, *, tmp_path: Path, input_: str, output: str, expected: bool
    ) -> None:
        path = tmp_path / PYPROJECT_TOML
        full_input = normalize_multi_line_str(
            f"""
            [project]
              dependencies = ["{input_}"]
            """,
            trailing=True,
        )
        write_text_and_add_modification(path, full_input)
        exp_output = normalize_multi_line_str(
            f"""
            [project]
              dependencies = ["{output}"]
            """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path=path)
            exp_result = (i >= 1) or expected
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output

    def test_sorting(self, *, tmp_path: Path) -> None:
        path = tmp_path / PYPROJECT_TOML
        full_input = normalize_multi_line_str(
            """
            [project]
              dependencies = ["c", "b", "a"]
            """,
            trailing=True,
        )
        write_text_and_add_modification(path, full_input)
        exp_output = normalize_multi_line_str(
            """
            [project]
              dependencies = ["a", "b", "c"]
            """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
