from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import SecretStr
from pytest import mark, param
from utilities.core import normalize_multi_line_str

from pre_commit_hooks.constants import ENVRC
from pre_commit_hooks.hooks.setup_direnv import _get_text, _run

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import SecretLike


class TestGetText:
    def test_main(self) -> None:
        result = _get_text()
        expected = normalize_multi_line_str("""
            # uv
            export UV_MANAGED_PYTHON='true'
            export UV_PRERELEASE='disallow'
            export UV_PYTHON='3.12'
            export UV_RESOLUTION='highest'
            export UV_VENV_CLEAR='true'
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
        """)
        assert result == expected

    @mark.parametrize("password", [param("password"), param(SecretStr("password"))])
    def test_index(self, *, password: SecretLike) -> None:
        result = _get_text(
            index_name="name", index_username="username", index_password=password
        )
        expected = normalize_multi_line_str("""
            # uv
            export UV_INDEX_NAME_USERNAME='username'
            export UV_INDEX_NAME_PASSWORD='password'
            export UV_MANAGED_PYTHON='true'
            export UV_PRERELEASE='disallow'
            export UV_PYTHON='3.12'
            export UV_RESOLUTION='highest'
            export UV_VENV_CLEAR='true'
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
        """)
        assert result == expected

    def test_native_tls(self) -> None:
        result = _get_text(native_tls=True)
        expected = normalize_multi_line_str("""
            # uv
            export UV_MANAGED_PYTHON='true'
            export UV_NATIVE_TLS='true'
            export UV_PRERELEASE='disallow'
            export UV_PYTHON='3.12'
            export UV_RESOLUTION='highest'
            export UV_VENV_CLEAR='true'
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
        """)
        assert result == expected


class TestSetupDirenv:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / ENVRC
        for i in range(2):
            result = _run(path=path)
            expected = i >= 1
            assert result is expected
            assert path.is_file()
