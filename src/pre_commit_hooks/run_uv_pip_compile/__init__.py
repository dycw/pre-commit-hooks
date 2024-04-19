from __future__ import annotations

from pathlib import Path
from re import sub
from subprocess import CalledProcessError, check_call
from tempfile import TemporaryDirectory

from click import command, option
from loguru import logger

from pre_commit_hooks.common import REQUIREMENTS_TXT


@command()
@option(
    "--python-version",
    help="The minimum Python version that should be supported by the compiled requirements",
)
def main(*, python_version: str | None) -> bool:
    """CLI for the `run-uv-pip-compile` hook."""
    return _process(python_version=python_version)


def _process(*, python_version: str | None) -> bool:
    curr = _read_requirements_txt(REQUIREMENTS_TXT)
    latest = _run_uv_pip_compile(python_version=python_version)
    if curr == latest:
        return True
    _write_requirements_txt(latest)
    return False


def _read_requirements_txt(path: Path, /) -> str | None:
    try:
        with path.open() as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def _run_uv_pip_compile(*, python_version: str | None) -> str:
    with TemporaryDirectory() as temp:
        temp_file = Path(temp, "requirements.txt")
        cmd = (
            [
                "uv",
                "pip",
                "compile",
                "--extra=dev",
                "--prerelease=disallow",
                "--quiet",
                f"--output-file={temp_file.as_posix()}",
                "--upgrade",
            ]
            + ([] if python_version is None else [f"--python-version={python_version}"])
            + [
                "pyproject.toml"  # don't use absolute path
            ]
        )
        try:
            _ = check_call(cmd)
        except CalledProcessError:
            logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
            raise
        with temp_file.open(mode="r") as fh:
            contents = fh.read()
        return _fix_header(contents, temp_file) + "\n"


def _fix_header(text: str, temp_file: Path, /) -> str:
    return "\n".join(_fix_header_line(line, temp_file) for line in text.splitlines())


def _fix_header_line(line: str, temp_file: Path, /) -> str:
    return sub(str(temp_file), temp_file.name, line)


def _write_requirements_txt(contents: str, /) -> None:
    with REQUIREMENTS_TXT.open(mode="w") as fh:
        _ = fh.write(contents)
