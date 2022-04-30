from pathlib import Path
from subprocess import check_output  # noqa: S404
from typing import Tuple

import click
from click import command
from click.decorators import argument


@command()
@argument("filenames", nargs=-1, type=click.Path(path_type=Path))
def main(filenames: Tuple[Path, ...]) -> int:
    results = [_process(f) for f in filenames if f.name == "Dockerfile"]
    return 0 if all(results) else 1


def _process(filename: Path) -> bool:
    with open(filename) as fh:
        current = fh.read()
    proposed = check_output(  # noqa: S603, S607
        ["dockfmt", "fmt", filename.as_posix()], text=True
    ).lstrip("\t\n")
    if current == proposed:
        return True
    else:
        with open(filename, mode="w") as fh:
            _ = fh.write(proposed)
        return False


if __name__ == "__main__":
    raise SystemExit(main())
