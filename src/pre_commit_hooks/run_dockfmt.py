#!/usr/bin/env python3
from argparse import ArgumentParser
from logging import basicConfig
from pathlib import Path
from subprocess import check_output
from sys import argv
from sys import stdout

basicConfig(level="INFO", stream=stdout)


def main() -> int:
    """CLI for the `run_dockfmt` hook."""
    parser = ArgumentParser()
    _ = parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)
    filenames = filter(_is_dockerfile, args.filenames[1:])
    results = list(map(_process, filenames))  # run all
    return 0 if all(results) else 1


def _is_dockerfile(filename: str) -> bool:
    return Path(filename).name == "Dockerfile"


def _process(filename: str) -> bool:
    with open(filename) as fh:
        current = fh.read()
    proposed = check_output(["dockfmt", "fmt", filename], text=True).lstrip(
        "\t\n"
    )
    if current == proposed:
        return True
    with open(filename, mode="w") as fh:
        _ = fh.write(proposed)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
