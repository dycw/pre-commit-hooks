from argparse import ArgumentParser
from contextlib import contextmanager
from importlib import resources
from subprocess import CalledProcessError  # noqa:S404
from subprocess import check_call  # noqa:S404
from sys import exit
from typing import Iterator
from typing import List
from typing import Optional
from typing import Sequence


def wrapped_check_call(args: List[str], file: str) -> None:
    check_call(args + [file])  # noqa: S603


def process_file(
    file: str,
    add_trailing_comma: List[str],
    autoflake: List[str],
    pyupgrade: List[str],
    reorder_python_imports: List[str],
    flake8: List[str],
    mypy: List[str],
) -> bool:
    try:
        wrapped_check_call(add_trailing_comma, file)
        wrapped_check_call(autoflake, file)
        wrapped_check_call(pyupgrade, file)
        wrapped_check_call(reorder_python_imports, file)
        wrapped_check_call(["yesqa"], file)
        wrapped_check_call(["black"], file)
        wrapped_check_call(flake8, file)
        wrapped_check_call(mypy, file)
    except CalledProcessError:
        return False
    else:
        return True


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    def read_call(name: str) -> List[str]:
        return resources.read_text("hooks.py_hooks", name).splitlines()

    add_trailing_comma = read_call("add_trailing_comma")
    autoflake = read_call("autoflake")
    pyupgrade = read_call("pyupgrade")
    reorder_python_imports = read_call("reorder_python_imports")

    @contextmanager
    def yield_call(cmd: str, file: str) -> Iterator[List[str]]:
        with resources.path("hooks.py_hooks", file) as path:
            yield [cmd, f"--config={path}"]

    with yield_call("flake8", ".flake8") as flake8, yield_call(
        "mypy",
        "mypy.ini",
    ) as mypy:
        result = all(
            process_file(
                file,
                add_trailing_comma,
                autoflake,
                pyupgrade,
                reorder_python_imports,
                flake8,
                mypy,
            )
            for file in args.filenames
        )
    return 0 if result else 1


if __name__ == "__main__":
    exit(main())
