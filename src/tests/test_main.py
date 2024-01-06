from __future__ import annotations

from pre_commit_hooks import __version__


def test_main() -> None:
    assert isinstance(__version__, str)
