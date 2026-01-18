from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command
from tomlkit import string
from tomlkit.items import Array
from utilities.click import CONTEXT_SETTINGS
from utilities.functions import ensure_str
from utilities.os import is_pytest
from utilities.packaging import Requirement
from utilities.types import PathLike

from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.utilities import (
    get_pyproject_dependencies,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.items import Array
    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@argument("paths", nargs=-1, type=utilities.click.Path())
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))


def _run(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        get_pyproject_dependencies(doc).map_array(_func_array)
    return len(modifications) == 0


def _func_array(array: Array, /) -> None:
    new: list[str] = []
    for curr_i in array:
        req = Requirement(ensure_str(curr_i))
        new.append(str(req))
    array.clear()
    for new_i in sorted(new):
        array.append(string(new_i))


if __name__ == "__main__":
    _main()
