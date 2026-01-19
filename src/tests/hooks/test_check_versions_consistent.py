from __future__ import annotations

from utilities.constants import HOUR
from utilities.pytest import throttle_test

from pre_commit_hooks.constants import BUMPVERSION_TOML
from pre_commit_hooks.hooks.check_versions_consistent import _run


class TestCheckVersionsConsistent:
    @throttle_test(duration=HOUR)
    def test_main(self) -> None:
        assert _run(path=BUMPVERSION_TOML)
