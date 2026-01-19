from __future__ import annotations

from collections.abc import Callable

from tomlkit.container import Container
from tomlkit.items import AoT, Array, Table
from utilities.packaging import Requirement
from utilities.types import StrDict
from utilities.version import Version2Or3

type ArrayLike = AoT | list[str] | list[StrDict]
type ContainerLike = Container | Table
type FuncRequirement = Callable[[Requirement], Requirement]
type TransformArray = Callable[[Array], None]
type VersionSet = dict[str, Version2Or3]


__all__ = [
    "ArrayLike",
    "ContainerLike",
    "FuncRequirement",
    "TransformArray",
    "VersionSet",
]
