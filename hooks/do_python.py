from argparse import ArgumentParser
from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from subprocess import CalledProcessError  # noqa:S404
from subprocess import check_call  # noqa:S404
from sys import exit
from typing import Iterator
from typing import Optional
from typing import Sequence


def process_file(file: str, add_trailing_comma: str, flake8: Path, mypy: Path) -> bool:
    try:
        check_call([add_trailing_comma, file])  # noqa: S603
        check_call(  # noqa:S603,S607
            [
                "autoflake",
                "--in-place",
                "--remove-all-unused-imports",
                "--remove-duplicate-keys",
                "--remove-unused-variables",
                file,
            ],
        )
        check_call(  # noqa:S603,S607
            ["pyupgrade", "--exit-zero-even-if-changed", "--py38-plus", file],
        )
        check_call(  # noqa:S603,S607
            [
                "reorder-python-imports",
                "--exit-zero-even-if-changed",
                "--py38-plus",
                file,
            ],
        )
        check_call(["yesqa", file])  # noqa:S603,S607
        check_call(["black", file])  # noqa:S603,S607
        check_call(["flake8", f"--config={flake8}", file])  # noqa:S603,S607
        check_call(["mypy", f"--config={mypy}", file])  # noqa:S603,S607
    except CalledProcessError:
        return False
    else:
        return True


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    def read_call(name: str) -> str:
        return resources.read_text("hooks.py_hooks", name).replace("\n", " ")

    add_trailing_comma = read_call("add_trailing_comma")

    @contextmanager
    def yield_config(name: str) -> Iterator[Path]:
        with resources.path("hooks.py_hooks", name) as path:
            yield path

    with yield_config(".flake8") as flake8, yield_config(
        "mypy.ini",
    ) as mypy:
        result = all(
            process_file(file, add_trailing_comma, flake8, mypy)
            for file in args.filenames
        )
    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
