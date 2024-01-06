from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from subprocess import check_output

import click
from click import argument, command


@command()
@argument(
    "paths",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, path_type=Path
    ),
)
def main(paths: tuple[Path, ...], /) -> bool:
    """CLI for the `run-dockfmt` hook."""
    results = list(_yield_outcomes(*paths))  # run all
    return all(results)


def _yield_outcomes(*paths: Path) -> Iterator[bool]:
    for path in paths:
        if path.name == "Dockerfile":
            yield _process(path)


def _process(path: Path, /) -> bool:
    with path.open() as fh:
        current = fh.read()
    strip = "\t\n"
    proposed = check_output(
        ["dockfmt", "fmt", path.as_posix()],  # noqa: S603, S607
        text=True,
    ).lstrip(strip)
    if current == proposed:
        return True
    with path.open(mode="w") as fh:
        _ = fh.write(proposed)
    return False
