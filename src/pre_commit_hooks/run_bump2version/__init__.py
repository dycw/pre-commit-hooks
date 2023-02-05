from hashlib import md5
from pathlib import Path
from re import MULTILINE, findall
from subprocess import (
    PIPE,
    STDOUT,
    CalledProcessError,
    check_call,
    check_output,
)

from beartype import beartype
from click import command, option
from loguru import logger
from semver import VersionInfo
from xdg import xdg_cache_home


@command()
@option(
    "--setup-cfg",
    is_flag=True,
    help="Read `setup.cfg` instead of `bumpversion.cfg`",
)
@beartype
def main(*, setup_cfg: bool) -> bool:
    """CLI for the `run_bump2version` hook."""
    return _process(setup_cfg=setup_cfg)


@beartype
def _process(*, setup_cfg: bool) -> bool:
    filename = "setup.cfg" if setup_cfg else ".bumpversion.cfg"
    path = Path(filename)
    current = _get_current_version(path)
    master = _get_master_version(filename)
    patched = master.bump_patch()
    if current in {master.bump_major(), master.bump_minor(), patched}:
        return True
    cmd = ["bump2version", "--allow-dirty", f"--new-version={patched}", "patch"]
    try:
        _ = check_call(cmd, stdout=PIPE, stderr=STDOUT)
    except CalledProcessError as error:
        if error.returncode != 1:
            logger.exception("Failed to run {!r}", " ".join(cmd))
    except FileNotFoundError:
        logger.exception(
            "Failed to run {!r}. Is `bump2version` installed?",
            " ".join(cmd),
        )
    else:
        _trim_trailing_whitespaces(path)
        return True
    return False


@beartype
def _get_current_version(path: Path, /) -> VersionInfo:
    with path.open() as fh:
        text = fh.read()
    return _parse_version(text)


@beartype
def _parse_version(text: str, /) -> VersionInfo:
    (line,) = findall(
        r"current_version = (\d+\.\d+\.\d+)$",
        text,
        flags=MULTILINE,
    )
    return VersionInfo.parse(line)


@beartype
def _get_master_version(filename: str, /) -> VersionInfo:
    repo = md5(
        Path.cwd().as_posix().encode(),
        usedforsecurity=False,
    ).hexdigest()
    commit = check_output(
        ["git", "rev-parse", "origin/master"],
        text=True,
    ).rstrip("\n")
    path = xdg_cache_home().joinpath(
        "pre-commit-hooks",
        "run-bump2version",
        repo,
        commit,
    )
    try:
        with path.open() as fh:
            version = VersionInfo.parse(fh.read())
    except FileNotFoundError:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = check_output(
            ["git", "show", f"{commit}:{filename}"],
            text=True,
        )
        version = _parse_version(text)
        with path.open(mode="w") as fh:
            _ = fh.write(str(version))
    return version


@beartype
def _trim_trailing_whitespaces(path: Path, /) -> None:
    with path.open() as fh:
        lines = fh.readlines()
    with path.open(mode="w") as fh:
        fh.writelines([line.rstrip(" ") for line in lines])
