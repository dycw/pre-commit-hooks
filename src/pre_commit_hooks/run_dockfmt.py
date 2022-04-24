from argparse import ArgumentParser
from logging import basicConfig
from subprocess import check_output  # noqa: S404
from sys import argv
from sys import stdout


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    parser = ArgumentParser()
    _ = parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)
    results = [_process(fn) is True for fn in args.filenames[1:]]
    return 0 if all(results) else 1


def _process(filename: str) -> bool:
    with open(filename) as fh:
        current = fh.read()
    proposed = check_output(  # noqa: S603, S607
        ["dockfmt", "fmt", filename], text=True
    ).lstrip("\t\n")
    if current == proposed:
        return True
    else:
        with open(filename, mode="w") as fh:
            _ = fh.write(proposed)
        return False


if __name__ == "__main__":
    raise SystemExit(main())
