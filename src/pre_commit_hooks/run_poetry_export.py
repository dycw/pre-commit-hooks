#!/usr/bin/env python3
from argparse import ArgumentParser
from subprocess import check_output  # noqa: S404
from typing import Optional


def main() -> int:
    parser = ArgumentParser()
    _ = parser.add_argument("--output-file")
    args = parser.parse_args()
    return int(not _process(output_file=args.output_file))


def _process(*, output_file: Optional[str]) -> bool:
    filename = "requirements.txt" if output_file is None else output_file
    try:
        current = _get_current_requirements(filename)
    except FileNotFoundError:
        return _write_new_requirements(filename)
    else:
        new = _get_new_requirements()
        if current == new:
            return True
        else:
            return _write_new_requirements(filename, contents=new)


def _get_current_requirements(filename: str) -> str:
    with open(filename) as fh:
        return fh.read()


def _get_new_requirements() -> str:
    return check_output(  # noqa: S603, S607
        ["poetry", "export", "-f", "requirements.txt"], text=True
    )


def _write_new_requirements(
    filename: str, *, contents: Optional[str] = None
) -> bool:
    with open(filename, mode="w") as fh:
        use = _get_new_requirements() if contents is None else contents
        _ = fh.write(use)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
