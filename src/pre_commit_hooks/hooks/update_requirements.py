from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from functools import total_ordering
from typing import TYPE_CHECKING, Any, Self, override

from pydantic import BaseModel
from utilities.version import (
    ParseVersionError,
    _VersionEmptySuffixError,
    _VersionNegativeMajorVersionError,
    _VersionNegativeMinorVersionError,
    _VersionZeroError,
)
from utilities.version import Version as Version3
from utilities.version import parse_version as parse_version3

if TYPE_CHECKING:
    from pathlib import Path

type TwoSidedVersions = tuple[Version2or3 | None, Version1or2 | None]
type Version1or2 = int | Version2
type Version2or3 = Version2 | Version3
type VersionSet = dict[str, Version2or3]


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


##


@dataclass(repr=False, frozen=True, slots=True)
@total_ordering
class Version2:
    """A version identifier."""

    major: int = 0
    minor: int = 0
    suffix: str | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if (self.major == 0) and (self.minor == 0):
            raise _VersionZeroError(major=self.major, minor=self.minor, patch=0)
        if self.major < 0:
            raise _VersionNegativeMajorVersionError(major=self.major)
        if self.minor < 0:
            raise _VersionNegativeMinorVersionError(minor=self.minor)
        if (self.suffix is not None) and (len(self.suffix) == 0):
            raise _VersionEmptySuffixError(suffix=self.suffix)

    def __le__(self, other: Any, /) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        self_as_tuple = (self.major, self.minor)
        other_as_tuple = (other.major, other.minor)
        return self_as_tuple <= other_as_tuple

    @override
    def __repr__(self) -> str:
        version = f"{self.major}.{self.minor}"
        if self.suffix is not None:
            version = f"{version}-{self.suffix}"
        return version

    def bump_major(self) -> Self:
        return type(self)(self.major + 1, 0)

    def bump_minor(self) -> Self:
        return type(self)(self.major, self.minor + 1)

    def with_suffix(self, *, suffix: str | None = None) -> Self:
        return replace(self, suffix=suffix)


def parse_version1_or_2(version: str, /) -> Version1or2:
    try:
        return parse_version2(version)
    except ParseVersionError:
        return int(version)


def parse_version2_or_3(version: str, /) -> Version2or3:
    try:
        return parse_version3(version)
    except ParseVersionError:
        return parse_version2(version)


def parse_version2(version: str, /) -> Version2:
    try:
        ((major, minor, suffix),) = _PARSE_VERSION2_PATTERN.findall(version)
    except ValueError:
        raise ParseVersionError(version=version) from None
    return Version2(int(major), int(minor), suffix=None if suffix == "" else suffix)


_PARSE_VERSION2_PATTERN = re.compile(r"^(\d+)\.(\d+)(?:-(\w+))?")
