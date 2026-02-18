from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.version import Version2, Version2Or3, Version3, parse_version_2_or_3

from pre_commit_hooks.click import (
    index_option,
    index_password_option,
    index_username_option,
    native_tls_flag,
    paths_argument,
)
from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.utilities import (
    get_pyproject_dependencies,
    get_version_set,
    run_all_maybe_raise,
    yield_toml_doc,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.packaging import Requirement
    from utilities.types import MaybeSequenceStr, PathLike, SecretLike

    from pre_commit_hooks.types import VersionSet


type _Version1or2 = int | Version2


@command(**CONTEXT_SETTINGS)
@paths_argument
@index_option
@index_username_option
@index_password_option
@native_tls_flag
def _main(
    *,
    paths: tuple[Path, ...],
    index: MaybeSequenceStr | None,
    index_username: str | None,
    index_password: SecretLike | None,
    native_tls: bool = False,
) -> None:
    if is_pytest():
        return
    versions = get_version_set(
        index=index,
        index_username=index_username,
        index_password=index_password,
        native_tls=native_tls,
    )
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            versions=versions,
            index=index,
            index_username=index_username,
            index_password=index_password,
            native_tls=native_tls,
        )
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PYPROJECT_TOML,
    versions: VersionSet | None = None,
    index: MaybeSequenceStr | None = None,
    index_username: str | None = None,
    index_password: SecretLike | None = None,
    native_tls: bool = False,
) -> bool:
    func = partial(
        _transform,
        versions=versions,
        index=index,
        index_username=index_username,
        index_password=index_password,
        native_tls=native_tls,
    )
    modifications: set[Path] = set()
    with yield_toml_doc(path, modifications=modifications) as doc:
        get_pyproject_dependencies(doc).map_requirements(func)
    return len(modifications) == 0


def _transform(
    requirement: Requirement,
    /,
    *,
    versions: VersionSet | None = None,
    index: MaybeSequenceStr | None = None,
    index_username: str | None = None,
    index_password: SecretLike | None = None,
    native_tls: bool = False,
) -> Requirement:
    if versions is None:
        versions_use = get_version_set(
            index=index,
            index_username=index_username,
            index_password=index_password,
            native_tls=native_tls,
        )
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
    try:
        fixed = parse_version_2_or_3(requirement["=="])
    except KeyError:
        fixed = None
    latest = versions_use.get(requirement.name)
    new_lower: Version2Or3 | None = None
    new_upper: _Version1or2 | None = None
    match lower, upper, fixed, latest:
        case None, None, None, None:
            pass
        case None, None, Version2() | Version3(), Version2() | Version3() | None:
            pass
        case None, None, None, Version2() | Version3():
            new_lower = latest
            new_upper = latest.bump_major().major
        case Version2() | Version3(), None, None, None:
            new_lower = lower
        case (Version2(), None, None, Version2()) | (
            Version3(),
            None,
            None,
            Version3(),
        ):
            new_lower = max(lower, latest)
        case None, int() | Version2(), None, None:
            new_upper = upper
        case None, int(), None, Version2():
            new_upper = max(upper, latest.bump_major().major)
        case None, Version2(), None, Version3():
            bumped = latest.bump_minor()
            new_upper = max(upper, Version2(bumped.major, bumped.minor))
        case (
            (Version2(), int(), None, None)
            | (Version3(), int(), None, None)
            | (Version3(), Version2(), None, None)
        ):
            new_lower = lower
            new_upper = upper
        case (Version2(), int(), None, Version2()) | (
            Version3(),
            int(),
            None,
            Version3(),
        ):
            new_lower = max(lower, latest)
            new_upper = new_lower.bump_major().major
        case Version3(), Version2(), None, Version3():
            new_lower = max(lower, latest)
            new_upper = new_lower.bump_minor().version2
        case never:
            raise NotImplementedError(never)
    if new_lower is not None:
        requirement = requirement.replace(">=", str(new_lower))
    if new_upper is not None:
        requirement = requirement.replace("<", str(new_upper))
    return requirement


def _parse_version_1_or_2(version: str, /) -> _Version1or2:
    try:
        return int(version)
    except ValueError:
        return Version2.parse(version)


if __name__ == "__main__":
    _main()
