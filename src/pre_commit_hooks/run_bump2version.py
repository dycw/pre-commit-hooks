#!/usr/bin/env python3
from argparse import ArgumentParser
from dataclasses import astuple, dataclass
from hashlib import md5
from logging import basicConfig, error
from pathlib import Path
from re import MULTILINE, findall
from subprocess import (
    PIPE,
    STDOUT,
    CalledProcessError,
    check_call,
    check_output,
)
from sys import stdout

basicConfig(level="INFO", stream=stdout)


def main() -> int:
    """CLI for the `run_bump2version` hook."""
    parser = ArgumentParser()
    _ = parser.add_argument("--setup-cfg", action="store_true")
    args = parser.parse_args()
    return int(not _process(setup_cfg=args.setup_cfg))


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
    except CalledProcessError as cperror:
        if cperror.returncode != 1:
            error("Failed to run %r", " ".join(cmd))
    except FileNotFoundError:
        error("Failed to run %r. Is `bump2version` installed?", " ".join(cmd))
    else:
        _trim_trailing_whitespaces(path)
        return True
    return False


def _get_current_version(path: Path, /) -> "Version":
    with path.open() as fh:
        text = fh.read()
    major, minor, patch = _read_versions(text)
    return Version(major, minor, patch)


def _read_versions(text: str, /) -> tuple[int, int, int]:
    (group,) = findall(
        r"current_version = (\d+)\.(\d+)\.(\d+)$",
        text,
        flags=MULTILINE,
    )
    major, minor, patch = map(int, group)
    return major, minor, patch


def _get_master_version(filename: str, /) -> "Version":
    repo = md5(
        Path.cwd().as_posix().encode(),
        usedforsecurity=False,
    ).hexdigest()
    commit = check_output(
        ["git", "rev-parse", "origin/master"],
        text=True,
    ).rstrip("\n")
    path = Path.home().joinpath(
        ".cache",
        "pre-commit-hooks",
        "run-bump2version",
        repo,
        commit,
    )
    try:
        with path.open() as fh:
            versions_str = fh.read()
        major, minor, patch = map(int, versions_str.split())
    except FileNotFoundError:
        path.parent.mkdir(parents=True, exist_ok=True)
        contents = check_output(
            ["git", "show", f"{commit}:{filename}"],
            text=True,
        )
        major, minor, patch = version_ints = _read_versions(contents)
        versions_str = " ".join(map(str, version_ints))
        with path.open(mode="w") as fh:
            _ = fh.write(versions_str)
    return Version(major, minor, patch)


def _trim_trailing_whitespaces(path: Path, /) -> None:
    with path.open() as fh:
        lines = fh.readlines()
    with path.open(mode="w") as fh:
        fh.writelines([line.rstrip(" ") for line in lines])


@dataclass(repr=False, frozen=True)
class Version:
    """A semantic version."""

    major: int
    minor: int
    patch: int

    def __repr__(self) -> str:
        return ".".join(map(str, astuple(self)))

    def __str__(self) -> str:
        return repr(self)

    def bump_major(self) -> "Version":
        """Bump the major part of the version."""
        return Version(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> "Version":
        """Bump the minor part of the version."""
        return Version(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> "Version":
        """Bump the patch part of the version."""
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)


if __name__ == "__main__":
    raise SystemExit(main())
