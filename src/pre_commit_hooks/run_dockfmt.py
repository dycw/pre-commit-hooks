from argparse import ArgumentParser
from logging import basicConfig
from re import search
from subprocess import check_call  # noqa: S404
from subprocess import check_output  # noqa: S404
from sys import argv
from sys import stdout
from typing import List


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    parser = ArgumentParser()
    _ = parser.add_argument("filenames", nargs="*", help="Filenames to check.")
    args = parser.parse_args(argv)
    results = [_process(fn) is True for fn in args.filenames[1:]]
    return 0 if all(results) else 1


def _process(filename: str) -> bool:
    cmd_diff = _make_command("D", filename)
    first, *rest = check_output(cmd_diff, text=True).splitlines()  # noqa: S603
    if not search(r"^diff .+ .+$", first):
        raise ValueError(f"First line {first!r} is unexpectedly different")
    if len(rest) == 0:
        return True
    else:
        _ = check_call(_make_command("w", filename))  # noqa: S603
        return False


def _make_command(flag: str, filename: str) -> List[str]:
    return ["dockfmt", "fmt", f"-{flag}", filename]


if __name__ == "__main__":
    raise SystemExit(main())
