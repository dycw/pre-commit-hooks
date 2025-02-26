from __future__ import annotations

from pathlib import Path
from re import sub
from subprocess import CalledProcessError, check_call
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Literal

from click import Choice, command, option
from loguru import logger

from pre_commit_hooks.common import REQUIREMENTS_TXT

if TYPE_CHECKING:
    from collections.abc import Iterable


@command()
@option(
    "--output-file",
    default=REQUIREMENTS_TXT,
    help="Write the compiled requirements to the given `requirements.txt` file",
)
@option("--extra", multiple=True, help="Optional dependencies")
@option(
    "--python-platform",
    type=Choice(["windows", "linux", "macos"], case_sensitive=False),
    help="The platform for which requirements should be resolved",
)
@option(
    "--python-version", default=None, help="The Python version to use for resolution"
)
def main(
    *,
    output_file: Path | str = REQUIREMENTS_TXT,
    extra: tuple[str, ...] = (),
    python_platform: Literal["windows", "linux", "macos"] | None = None,
    python_version: str | None = None,
) -> bool:
    """CLI for the `run-uv-pip-compile` hook."""
    return _process(
        output_file=Path(output_file),
        extra=None if len(extra) == 0 else list(extra),
        python_platform=python_platform,
        python_version=python_version,
    )


def _process(
    *,
    extra: Iterable[str] | None = None,
    output_file: Path = REQUIREMENTS_TXT,
    python_platform: Literal["windows", "linux", "macos"] | None = None,
    python_version: str | None = None,
) -> bool:
    curr = _read_requirements_txt(output_file)
    latest = _run_uv_pip_compile(
        extra=extra, python_platform=python_platform, python_version=python_version
    )
    if curr == latest:
        return True
    _write_requirements_txt(latest, path=output_file)
    return False


def _read_requirements_txt(path: Path, /) -> str | None:
    try:
        with path.open() as fh:
            return fh.read()
    except FileNotFoundError:
        return None


def _run_uv_pip_compile(
    *,
    extra: Iterable[str] | None = None,
    python_platform: Literal["windows", "linux", "macos"] | None = None,
    python_version: str | None = None,
) -> str:
    cmd: list[str] = [
        "uv",
        "pip",
        "compile",
        "--extra=dev",
        "--prerelease=explicit",
        "--quiet",
        "--upgrade",
    ]
    if extra is not None:
        cmd.extend(f"--extra={e}" for e in extra)
    if python_platform is not None:
        cmd.append(f"--python-platform={python_platform}")
    if python_version is not None:
        cmd.append(f"--python-version={python_version}")
    with TemporaryDirectory() as temp:
        temp_file = Path(temp, "temp.txt")
        cmd.extend([
            f"--output-file={temp_file.as_posix()}",
            "pyproject.toml",  # don't use absolute path
        ])
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


def _write_requirements_txt(contents: str, /, *, path: Path = REQUIREMENTS_TXT) -> None:
    with path.open(mode="w") as fh:
        _ = fh.write(contents)
