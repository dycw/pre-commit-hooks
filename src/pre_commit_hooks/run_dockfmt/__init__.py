from pathlib import Path
from subprocess import check_output

import click
from beartype import beartype
from click import argument, command


@command()
@argument(
    "filenames",
    nargs=-1,
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        path_type=Path,
    ),
)
@beartype
def main(filenames: tuple[Path, ...]) -> int:
    """CLI for the `run_dockfmt` hook."""
    dockerfiles = (p for p in filenames if p.name == "Dockerfile")
    results = list(map(_process, dockerfiles))  # run all
    return all(results)


@beartype
def _process(path: Path, /) -> bool:
    with path.open() as fh:
        current = fh.read()
    strip = "\t\n"
    proposed = check_output(
        ["dockfmt", "fmt", path.as_posix()],
        text=True,
    ).lstrip(
        strip,
    )
    if current == proposed:
        return True
    with path.open(mode="w") as fh:
        _ = fh.write(proposed)
    return False
