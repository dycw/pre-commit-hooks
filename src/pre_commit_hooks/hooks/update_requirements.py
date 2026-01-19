from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

import utilities.click
from click import argument, command, option
from utilities.click import CONTEXT_SETTINGS, ListStrs
from utilities.functions import max_nullable
from utilities.os import is_pytest
from utilities.subprocess import uv_pip_list
from utilities.version import Version2, Version2Or3, Version3, parse_version_2_or_3

from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.utilities import (
    get_pyproject_dependencies,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from pathlib import Path

    from utilities.packaging import Requirement
    from utilities.types import PathLike, StrDict


type Version1or2 = int | Version2
type VersionSet = dict[str, Version2Or3]


@command(**CONTEXT_SETTINGS)
@argument("paths", nargs=-1, type=utilities.click.Path())
@option("--index", type=ListStrs(), default=None)
@option("--native-tls", is_flag=True, default=False)
def _main(
    *, paths: tuple[Path, ...], index: list[str] | None = None, native_tls: bool = False
) -> None:
    if is_pytest():
        return
    versions = _get_versions(index=index, native_tls=native_tls)
    run_all_maybe_raise(
        *(
            partial(_run, path=p, versions=versions, index=index, native_tls=native_tls)
            for p in paths
        )
    )


def _get_versions(
    *, index: list[str] | None = None, native_tls: bool = False
) -> dict[str, Version2Or3]:
    out: StrDict = {}
    for item in uv_pip_list(index=index, native_tls=native_tls):
        match item.version, item.latest_version:
            case Version2(), Version2() | None:
                out[item.name] = max_nullable([item.version, item.latest_version])
            case Version3(), Version3() | None:
                out[item.name] = max_nullable([item.version, item.latest_version])
            case _:
                raise TypeError(item.version, item.latest_version)
    return out


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    versions: VersionSet | None = None,
    index: list[str] | None = None,
    native_tls: bool = False,
) -> bool:
    func = partial(_transform, versions=versions, index=index, native_tls=native_tls)
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        get_pyproject_dependencies(doc).map_requirements(func)
    return len(modifications) == 0


def _transform(
    requirement: Requirement,
    /,
    *,
    versions: VersionSet | None = None,
    index: list[str] | None = None,
    native_tls: bool = False,
) -> Requirement:
    if versions is None:
        versions_use = _get_versions(index=index, native_tls=native_tls)
    else:
        versions_use = versions
    try:
        lower = parse_version_2_or_3(requirement[">="])
    except KeyError:
        lower = None
    try:
        upper = _parse_version_1_or_2(requirement["<"])
    except KeyError:
        upper = None
    latest = versions_use.get(requirement.name)
    new_lower: Version2Or3 | None = None
    new_upper: Version1or2 | None = None
    match lower, upper, latest:
        case None, None, None:
            ...
        case None, None, Version2() | Version3():
            new_lower = latest
            new_upper = latest.bump_major().major
        case Version2() | Version3(), None, None:
            new_lower = lower
        case (Version2(), None, Version2()) | (Version3(), None, Version3()):
            new_lower = max(lower, latest)
        case None, int() | Version2(), None:
            new_upper = upper
        case None, int(), Version2():
            new_upper = max(upper, latest.bump_major().major)
        case None, Version2(), Version3():
            bumped = latest.bump_minor()
            new_upper = max(upper, Version2(bumped.major, bumped.minor))
        case (
            (Version2(), int(), None)
            | (Version3(), int(), None)
            | (Version3(), Version2(), None)
        ):
            new_lower = lower
            new_upper = lower.bump_major().major
        case (
            (Version2(), int(), Version2())
            | (Version3(), int(), Version3())
            | (Version3(), Version2(), Version3())
        ):
            new_lower = max(lower, latest)
            new_upper = new_lower.bump_major().major
        case never:
            raise NotImplementedError(never)
    if new_lower is not None:
        requirement = requirement.replace(">=", str(new_lower))
    if new_upper is not None:
        requirement = requirement.replace("<", str(new_upper))
    return requirement


def _parse_version_1_or_2(version: str, /) -> Version1or2:
    try:
        return int(version)
    except ValueError:
        return Version2.parse(version)


if __name__ == "__main__":
    _main()
