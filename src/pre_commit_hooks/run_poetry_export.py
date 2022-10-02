#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output  # noqa: S404


def main() -> int:
    parser = ArgumentParser()
    _ = parser.add_argument(
        "--filename",
        default="requirements.txt",
        help="The name of the output file.",
    )
    _ = parser.add_argument(
        "--without-hashes",
        action="store_true",
        help="Exclude hashes from the exported file.",
    )
    _ = parser.add_argument(
        "--dev", action="store_true", help="Include development dependencies."
    )
    args = parser.parse_args()
    return int(
        not _process(
            args.filename, without_hashes=args.without_hashes, dev=args.dev
        )
    )


def _process(
    filename: str, *, without_hashes: bool = False, dev: bool = False
) -> bool:
    try:
        current = _get_current_requirements(filename)
    except FileNotFoundError:
        return _write_new_requirements(
            filename, without_hashes=without_hashes, dev=dev
        )
    else:
        new = _get_new_requirements(without_hashes=without_hashes, dev=dev)
        if current == new:
            return True
        else:
            return _write_new_requirements(filename, contents=new)


def _get_current_requirements(filename: str) -> str:
    with open(filename) as fh:
        return fh.read()


def _get_new_requirements(
    *, without_hashes: bool = False, dev: bool = False
) -> str:
    cmd = ["poetry", "export", "-f", "requirements.txt"]
    if without_hashes:
        cmd.append("--without-hashes")
    if dev:
        cmd.append("--dev")
    contents = check_output(cmd, text=True)  # noqa: S603
    return "" if contents == "\n" else contents


def _write_new_requirements(
    filename: str,
    *,
    without_hashes: bool = False,
    dev: bool = False,
    contents: str | None = None,
) -> bool:
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, mode="w") as fh:
        if contents is None:
            use = _get_new_requirements(without_hashes=without_hashes, dev=dev)
        else:
            use = contents
        _ = fh.write(use)
        return False


if __name__ == "__main__":
    raise SystemExit(main())
