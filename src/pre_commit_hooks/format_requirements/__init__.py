from __future__ import annotations

from typing import TYPE_CHECKING, override

from click import argument, command
from libcst.matchers import Index as MIndex
from libcst.matchers import Name as MName
from libcst.matchers import Subscript as MSubscript
from libcst.matchers import SubscriptElement as MSubscriptElement
from libcst.matchers import matches
from libcst.metadata import MetadataWrapper
from loguru import logger
from packaging._tokenizer import ParserSyntaxError
from packaging.markers import Marker
from packaging.requirements import InvalidRequirement, Requirement, _parse_requirement
from packaging.specifiers import Specifier, SpecifierSet
from tomlkit import dumps, inline_table, loads
from tomlkit.items import Array, Table
from utilities.atomicwrites import writer
from utilities.click import FilePath
from utilities.version import Version, parse_version

from pre_commit_hooks.common import PYPROJECT_TOML

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument


@command()
@argument("paths", nargs=-1, type=FilePath)
def main(*, paths: tuple[Path, ...]) -> bool:
    """CLI for the `format_requirements` hook."""
    results = list(map(_process, paths))
    return all(results)


def _process(path: Path, /) -> bool:
    if path != PYPROJECT_TOML:
        return True
    doc = loads(path.read_text())
    expected = _format(path)
    if doc == expected:
        return True
    with writer(path, overwrite=True) as temp:
        _ = temp.write_text(dumps(doc))
    return False


def _format(path: Path, /) -> TOMLDocument:
    doc = loads(path.read_text())
    project = doc["project"]
    assert isinstance(project, Table)
    dependencies = project["dependencies"]
    assert isinstance(dependencies, Array)
    assert all(isinstance(d, str) for d in dependencies), dependencies
    project["dependencies"] = list(map(str, map(_CustomRequirement, dependencies)))
    return doc


class _CustomRequirement(Requirement):
    @override
    def __init__(self, requirement_string: str) -> None:
        super().__init__(requirement_string)
        try:
            parsed = _parse_requirement(requirement_string)
        except ParserSyntaxError as e:
            raise InvalidRequirement(str(e)) from e
        self.specifier = _CustomSpecifierSet(parsed.specifier)

    @override
    def __str__(self) -> str:
        return " ".join(self._iter_parts(self.name))


class _CustomSpecifierSet(SpecifierSet):
    @override
    def __str__(self) -> str:
        specs = sorted(self._specs, key=self._key)
        return ", ".join(map(str, specs))

    def _key(self, spec: Specifier, /) -> int:
        return [">=", "<"].index(spec.operator)


__all__ = ["main"]
