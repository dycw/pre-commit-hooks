from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command, option
from ordered_set import OrderedSet
from pydantic import BaseModel
from utilities.click import CONTEXT_SETTINGS, ListStrs
from utilities.os import is_pytest
from utilities.subprocess import run
from utilities.version import Version2, Version2Error, Version3

from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.utilities import (
    get_pyproject_dependencies,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.types import PathLike


type TwoSidedVersions = tuple[Version23 | None, Version12 | None]
type Version12 = int | Version2
type Version23 = Version2 | Version3
type VersionSet = dict[str, Version23]


@command(**CONTEXT_SETTINGS)
@argument("paths", nargs=-1, type=utilities.click.Path())
@option("--indexes", type=ListStrs(), default=None)
@option("--native-tls", is_flag=True, default=False)
def _main(
    *,
    paths: tuple[Path, ...],
    indexes: list[str] | None = None,
    native_tls: bool = False,
) -> None:
    if is_pytest():
        return
    _get_versions(indexes=indexes, native_tls=native_tls)
    run_all_maybe_raise(*(partial(_run, path=p) for p in paths))


def _get_versions(
    *, indexes: list[str] | None = None, native_tls: bool = False
) -> VersionSet:
    head: list[str] = ["uv", "pip", "list", "--format", "json"]
    tail: list[str] = ["--strict"]
    if len(indexes) >= 1:
        tail.extend(["--index", ",".join(indexes)])
    if native_tls:
        tail.append("--native-tls")
    json1 = run(*head, *tail, return_=True)
    models1 = TypeAdapter(list[PipListOutput]).validate_json(json1)
    versions1 = {p.name: parse_version2_or_3(p.version) for p in models1}
    json2 = run(*head, "--outdated", *tail, return_=True)
    models2 = TypeAdapter(list[PipListOutdatedOutput]).validate_json(json2)
    versions2 = {p.name: parse_version2_or_3(p.latest_version) for p in models2}
    out: StrDict = {}
    for key in set(versions1) | set(versions2):
        out[key] = max_nullable([versions1.get(key), versions2.get(key)])
    return out


class PipListOutput(BaseModel):
    name: str
    version: str
    editable_project_location: Path | None = None


class PipListOutdatedOutput(BaseModel):
    name: str
    version: str
    latest_version: str
    latest_filetype: str


_ = PipListOutput.model_rebuild()
_ = PipListOutdatedOutput.model_rebuild()


def _run(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        get_pyproject_dependencies(doc).map_requirements(_func_req)
    return len(modifications) == 0


##


def parse_version1_or_2(version: str, /) -> Version12:
    try:
        return int(version)
    except ValueError:
        return Version2.parse(version)


def parse_version2_or_3(version: str, /) -> Version23:
    try:
        return Version2.parse(version)
    except Version2Error:
        return Version3.parse(version)


if __name__ == "__main__":
    _main()
