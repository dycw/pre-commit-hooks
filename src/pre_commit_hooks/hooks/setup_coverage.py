from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from pre_commit_hooks.constants import COVERAGERC_TOML, paths_argument
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_array,
    get_set_table,
    merge_paths,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=COVERAGERC_TOML)
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = COVERAGERC_TOML) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        html = get_set_table(doc, "html")
        html["directory"] = ".coverage/html"
        report = get_set_table(doc, "report")
        exclude_also = get_set_array(report, "exclude_also")
        ensure_contains(exclude_also, "@overload", "if TYPE_CHECKING:")
        report["skip_covered"] = True
        report["skip_empty"] = True
        run = get_set_table(doc, "run")
        run["branch"] = True
        run["data_file"] = ".coverage/data"
        run["parallel"] = True
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
