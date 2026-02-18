from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from tomlkit.items import Array
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, read_text
from utilities.types import PathLike

from pre_commit_hooks.click import paths_argument
from pre_commit_hooks.constants import PYTEST_TOML
from pre_commit_hooks.utilities import (
    get_table,
    merge_paths,
    re_insert_array,
    re_insert_table,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYTEST_TOML)
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths_use))


def _run(*, path: PathLike = PYTEST_TOML) -> bool:
    init = read_text(path)
    with yield_toml_doc(path) as doc:
        pytest = get_table(doc, "pytest")
        re_insert_table(pytest)
        for value in pytest.values():
            if isinstance(value, Array):
                re_insert_array(value)
    return read_text(path) == init


if __name__ == "__main__":
    _main()
