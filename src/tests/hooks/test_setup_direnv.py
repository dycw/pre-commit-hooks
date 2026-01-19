from __future__ import annotations

from typing import TYPE_CHECKING

from utilities.text import strip_and_dedent

from pre_commit_hooks.constants import ENVRC
from pre_commit_hooks.hooks.setup_direnv import _get_text, _run

if TYPE_CHECKING:
    from pathlib import Path


class TestGetText:
    def test_main(self) -> None:
        result = _get_text()
        expected = strip_and_dedent(
            """
            # uv
            export UV_MANAGED_PYTHON='true'
            export UV_PRERELEASE='disallow'
            export UV_PYTHON='3.12'
            export UV_RESOLUTION='highest'
            export UV_VENV_CLEAR=1
            if ! command -v uv >/dev/null 2>&1; then
            \techo_date "ERROR: 'uv' not found" && exit 1
            fi
            activate='.venv/bin/activate'
            if [ -f $activate ]; then
            \t. $activate
            else
            \tuv venv
            fi
            uv sync --all-extras --all-groups --active --locked
        """,
            trailing=True,
        )
        assert result == expected


class TestSetupDirenv:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / ENVRC
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
