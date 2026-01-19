from __future__ import annotations

from utilities.constants import HOUR
from utilities.pytest import skipif_ci, throttle_test

from pre_commit_hooks.hooks.run_prek_autoupdate import _run


class TestRunPrekAutoUpdate:
    @skipif_ci
    @throttle_test(duration=HOUR)
    def test_main(self) -> None:
        assert _run(throttle=False)
