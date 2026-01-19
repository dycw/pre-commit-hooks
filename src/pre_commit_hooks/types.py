from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from tomlkit.container import Container
from tomlkit.items import AoT, Array, Table
from utilities.packaging import Requirement
from utilities.types import StrDict

type ArrayLike = AoT | list[str] | list[StrDict]
type ContainerLike = Container | Table


type GitHubOrGitea = Literal["github", "gitea"]


type FuncRequirement = Callable[[Requirement], Requirement]
type TransformArray = Callable[[Array], None]


__all__ = [
    "ArrayLike",
    "ContainerLike",
    "FuncRequirement",
    "GitHubOrGitea",
    "TransformArray",
]
