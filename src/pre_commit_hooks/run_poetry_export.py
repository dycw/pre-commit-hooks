from logging import basicConfig
from subprocess import check_output  # noqa: S404
from sys import stdout
from typing import Optional


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    return int(not _process())


def _process() -> bool:
    try:
        current = _get_current_requirements()
    except FileNotFoundError:
        return _write_new_requirements()
    else:
        new = _get_new_requirements()
        if current == new:
            return True
        else:
            return _write_new_requirements(contents=new)


def _get_filename() -> str:
    return "requirements.txt"


def _get_current_requirements() -> str:
    with open(_get_filename()) as fh:
        return fh.read()


def _get_new_requirements() -> str:
    return check_output(  # noqa: S603, S607
        ["poetry", "export", "-f", "requirements.txt"], text=True
    ).rstrip("\n")


def _write_new_requirements(*, contents: Optional[str] = None) -> bool:
    use = _get_new_requirements() if contents is None else contents
    with open(_get_filename(), mode="w") as fh:
        _ = fh.write(use)
    return False


if __name__ == "__main__":
    raise SystemExit(main())
