from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, snake_case
from utilities.types import PathLike

from pre_commit_hooks.constants import (
    COVERAGERC_TOML,
    PYTEST_TOML,
    paths_argument,
    python_package_name_internal_option,
)
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_array,
    get_set_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@python_package_name_internal_option
def _main(
    *, paths: tuple[Path, ...], python_package_name_internal: str | None = None
) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYTEST_TOML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, package_name=python_package_name_internal)
        for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PYTEST_TOML, package_name: str | None = None) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        pytest = get_set_table(doc, "pytest")
        addopts = get_set_array(pytest, "addopts")
        ensure_contains(
            addopts,
            "-ra",
            "-vv",
            "--color=auto",
            "--durations=10",
            "--durations-min=10",
        )
        pytest["asyncio_default_fixture_loop_scope"] = "function"
        pytest["asyncio_mode"] = "auto"
        pytest["collect_imported_tests"] = False
        pytest["empty_parameter_set_mark"] = "fail_at_collect"
        filterwarnings = get_set_array(pytest, "filterwarnings")
        ensure_contains(
            filterwarnings,
            "error",
            "ignore::DeprecationWarning",
            "ignore::ResourceWarning",
            "ignore::RuntimeWarning",
        )
        pytest["minversion"] = "9.0"
        pytest["strict"] = True
        testpaths = get_set_array(pytest, "testpaths")
        ensure_contains(testpaths, "src/tests")
        pytest["timeout"] = "600"
        pytest["xfail_strict"] = True
    if package_name is not None:
        _add_coverage_opts(package_name, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_coverage_opts(
    package_name: str,
    /,
    *,
    path: PathLike = PYTEST_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    path = Path(path)
    with yield_toml_doc(path, modifications=modifications) as doc:
        pytest = get_set_table(doc, "pytest")
        addopts = get_set_array(pytest, "addopts")
        ensure_contains(
            addopts,
            f"--cov={snake_case(package_name)}",
            f"--cov-config={path.parent / COVERAGERC_TOML}",
            "--cov-report=html",
        )


if __name__ == "__main__":
    _main()
