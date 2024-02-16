from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError, check_call
from tempfile import TemporaryDirectory

from click import command, option
from loguru import logger

from pre_commit_hooks.common import PYPROJECT_TOML, REQUIREMENTS_TXT


@command()
@option(
    "--python-version",
    help="The minimum Python version that should be supported by the compiled requirements",
)
def main(*, python_version: str | None) -> bool:
    """CLI for the `run-uv-pip-compile` hook."""
    return _process(python_version=python_version)


def _process(*, python_version: str | None) -> bool:
    curr = _get_requirements()
    latest = _run_uv_pip_compile(python_version=python_version)
    if curr == latest:
        return True
    _write_requirements_txt(latest)
    return False


def _get_requirements() -> str:
    try:
        with REQUIREMENTS_TXT.open(mode="r") as fh:
            return fh.read()
    except FileNotFoundError:
        logger.exception("requirements.txt not found")
        raise


def _run_uv_pip_compile(*, python_version: str | None) -> str:
    with TemporaryDirectory() as temp:
        temp_file = Path(temp, "requirements.txt")
        cmd = (
            [
                "uv",
                "pip",
                "compile",
                "--all-extras",
                "--generate-hashes",
                "--no-emit-index-url",
                "--no-emit-trusted-host",
                f"--output-file={temp_file.as_posix()}",
                "--prerelease=disallow",
            ]
            + ([] if python_version is None else [f"--python-version={python_version}"])
            + ["--quiet", "--upgrade", str(PYPROJECT_TOML)]
        )
        try:
            _ = check_call(cmd)  # noqa: S603
        except CalledProcessError:
            logger.exception("Failed to run {cmd!r}", cmd=" ".join(cmd))
            raise
        with temp_file.open(mode="r") as fh:
            return fh.read()


def _write_requirements_txt(contents: str, /) -> None:
    with REQUIREMENTS_TXT.open(mode="w") as fh:
        _ = fh.write(contents)
