from __future__ import annotations

from typing import TYPE_CHECKING

from pytest import mark, param
from utilities.packaging import Requirement
from utilities.text import strip_and_dedent
from utilities.version import Version2, Version3

from pre_commit_hooks.hooks.update_requirements import _run
from pre_commit_hooks.utilities import write_text

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.version import Version2Or3

    from pre_commit_hooks.hooks.update_requirements import VersionSet


class TestRun:
    @mark.parametrize(
        ("input_", "latest", "output", "expected"),
        [
            param("package", None, "package", True),
            param("package", Version2(1, 2), "package>=1.2, <2", False),
            param("package", Version3(1, 2, 3), "package>=1.2.3, <2", False),
            param("package>=1.2", None, "package>=1.2", True),
            param("package>=1.2", Version2(1, 2), "package>=1.2", True),
            param("package>=1.2", Version2(1, 3), "package>=1.3", False),
            param("package>=1.2.3", None, "package>=1.2.3", True),
            param("package>=1.2.3", Version3(1, 2, 3), "package>=1.2.3", True),
            param("package>=1.2.3", Version3(1, 2, 4), "package>=1.2.4", False),
            param("package<2", None, "package<2", True),
            param("package<2", Version2(1, 2), "package<2", True),
            param("package<2", Version2(2, 3), "package<3", False),
            param("package<1.3", None, "package<1.3", True),
            param("package<1.3", Version3(1, 2, 3), "package<1.3", True),
            param("package<1.3", Version3(1, 3, 0), "package<1.4", False),
            param("package>=1.2, <2", None, "package>=1.2, <2", True),
            param("package>=1.2, <2", Version2(1, 2), "package>=1.2, <2", True),
            param("package>=1.2, <2", Version2(1, 3), "package>=1.3, <2", False),
            param("package>=1.2.3, <1.3", None, "package>=1.2.3, <1.3", True),
            param(
                "package>=1.2.3, <1.3", Version3(1, 2, 3), "package>=1.2.3, <1.3", True
            ),
            param(
                "package>=1.2.3, <1.3", Version3(1, 2, 4), "package>=1.2.4, <1.3", False
            ),
            param("package>=1.2.3, <2", None, "package>=1.2.3, <2", True),
            param("package>=1.2.3, <2", Version3(1, 2, 3), "package>=1.2.3, <2", True),
            param("package>=1.2.3, <2", Version3(1, 2, 4), "package>=1.2.4, <2", False),
            param(
                "package[extra]>=1.2.3, <1.3", None, "package[extra]>=1.2.3, <1.3", True
            ),
            param(
                "package[extra]>=1.2.3, <1.3",
                Version3(1, 2, 3),
                "package[extra]>=1.2.3, <1.3",
                True,
            ),
            param(
                "package[extra]>=1.2.3, <1.3",
                Version3(1, 2, 4),
                "package[extra]>=1.2.4, <1.3",
                False,
            ),
        ],
    )
    def test_main(
        self,
        *,
        tmp_path: Path,
        input_: str,
        latest: Version2Or3 | None,
        output: str,
        expected: bool,
    ) -> None:
        path = tmp_path / "file.toml"
        full_input = strip_and_dedent(
            f"""
            [project]
              dependencies = ["{input_}"]
            """,
            trailing=True,
        )
        write_text(path, full_input)
        exp_output = strip_and_dedent(
            f"""
            [project]
              dependencies = ["{output}"]
            """,
            trailing=True,
        )
        req = Requirement(input_)
        versions: VersionSet = {}
        if latest is not None:
            versions[req.name] = latest
        for i in range(2):
            result = _run(path=path, versions=versions)
            exp_result = (i >= 1) or expected
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
