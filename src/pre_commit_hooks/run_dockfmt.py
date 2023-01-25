#!/usr/bin/env python3
from argparse import ArgumentParser
from logging import basicConfig
from pathlib import Path
from subprocess import check_output
from sys import argv, stdout

basicConfig(level="INFO", stream=stdout)


def main() -> int:
    """CLI for the `run_dockfmt` hook."""
    parser = ArgumentParser()
    _ = parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)
    paths = map(Path, args.filenames[1:])
    paths = filter(_is_dockerfile, paths)
    results = list(map(_process, paths))  # run all
    return 0 if all(results) else 1


def _is_dockerfile(path: Path, /) -> bool:
    return path.name == "Dockerfile"


def _process(path: Path, /) -> bool:
    with path.open() as fh:
        current = fh.read()
    proposed = check_output(
        ["dockfmt", "fmt", path.as_posix()],
        text=True,
    ).lstrip(
        "\t\n",
    )
    if current == proposed:
        return True
    with path.open(mode="w") as fh:
        _ = fh.write(proposed)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
