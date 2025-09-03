from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

import utilities.click
from click import argument, command
from packaging._tokenizer import ParserSyntaxError
from packaging.requirements import (
    InvalidRequirement,
    Requirement,
    _parse_requirement,  # pyright: ignore[reportPrivateImportUsage]
)
from packaging.specifiers import Specifier, SpecifierSet
from tomlkit import array, dumps, loads, string
from tomlkit.items import Array, Table

from pre_commit_hooks.common import run_all, write_text

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument


@command()
@argument("paths", nargs=-1, type=utilities.click.Path())
def main(*, paths: tuple[Path, ...]) -> bool:
    """CLI for the `format-requirements` hook."""
    return run_all(map(_process, paths))


def _process(path: Path, /) -> bool:
    doc = loads(path.read_text())
    expected = _format_path(path)
    return True if doc == expected else write_text(path, dumps(expected))


def _format_path(path: Path, /) -> TOMLDocument:
    doc = loads(path.read_text())
    if isinstance(dep_grps := doc.get("dependency-groups"), Table):
        for key, value in dep_grps.items():
            if isinstance(value, Array):
                dep_grps[key] = _format_array(value)
    if isinstance(project := doc["project"], Table):
        if isinstance(deps := project["dependencies"], Array):
            project["dependencies"] = _format_array(deps)
        if isinstance(optional := project.get("optional-dependencies"), Table):
            for key, value in optional.items():
                if isinstance(value, Array):
                    optional[key] = _format_array(value)
    return doc


def _format_array(dependencies: Array, /) -> Array:
    new = array().multiline(multiline=True)
    new.extend(map(_format_item, dependencies))
    return new


def _format_item(item: Any, /) -> Any:
    if not isinstance(item, str):
        return item
    return string(str(_CustomRequirement(item)))


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
    def _iter_parts(self, name: str) -> Iterator[str]:
        yield name
        if self.extras:
            formatted_extras = ",".join(sorted(self.extras))
            yield f"[{formatted_extras}]"
        if self.specifier:
            yield f" {self.specifier}"
        if self.url:
            yield f"@ {self.url}"
            if self.marker:
                yield " "
        if self.marker:
            yield f"; {self.marker}"


class _CustomSpecifierSet(SpecifierSet):
    @override
    def __str__(self) -> str:
        specs = sorted(self._specs, key=self._key)
        return ", ".join(map(str, specs))

    def _key(self, spec: Specifier, /) -> int:
        return [">=", "<"].index(spec.operator)


__all__ = ["main"]
