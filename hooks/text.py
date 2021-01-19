from argparse import ArgumentParser
from subprocess import CalledProcessError  # noqa:S404
from subprocess import check_call  # noqa:S404
from sys import exit
from typing import Optional
from typing import Sequence


def process_file(file: str) -> bool:
    try:
        check_call(["check-merge-conflict", file])  # noqa:S603,S607
        check_call(["check-vcs-permalinks", file])  # noqa:S603,S607
        check_call(["detect-private-key", file])  # noqa:S603,S607
        check_call(["end-of-file-fixer", file])  # noqa:S603,S607
        check_call(["fix-byte-order-marker", file])  # noqa:S603,S607
        check_call(["mixed-line-ending", "--fix=lf", file])  # noqa:S603,S607
        check_call(["trailing-whitespace-fixer", file])  # noqa:S603,S607
    except CalledProcessError:
        return False
    else:
        return True


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)
    result = all(process_file(file) for file in args.filenames)
    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
