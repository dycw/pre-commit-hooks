from argparse import ArgumentParser
from dataclasses import astuple
from dataclasses import dataclass
from logging import basicConfig
from logging import error
from re import MULTILINE
from re import findall
from subprocess import PIPE  # noqa: S404
from subprocess import STDOUT  # noqa: S404
from subprocess import CalledProcessError  # noqa: S404
from subprocess import check_call  # noqa: S404
from subprocess import check_output  # noqa: S404
from sys import stdout


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--setup-cfg", action="store_true")
    args = parser.parse_args()
    return int(not _process(setup_cfg=args.setup_cfg))


def _process(*, setup_cfg: bool) -> bool:
    filename = "setup.cfg" if setup_cfg else ".bumpversion.cfg"
    with open(filename) as fh:
        current = _read_version(fh.read())
    _ = check_call(  # noqa: S603, S607
        ["git", "fetch", "--all"], stdout=PIPE, stderr=STDOUT
    )
    commit = check_output(  # noqa: S603, S607
        ["git", "rev-parse", "origin/master"], text=True
    ).rstrip("\n")
    master = _read_version(
        check_output(  # noqa: S603, S607
            ["git", "show", f"{commit}:{filename}"], text=True
        )
    )
    patched = master.bump_patch()
    if current in {master.bump_major(), master.bump_minor(), patched}:
        return True
    else:
        cmd = [
            "bump2version",
            "--allow-dirty",
            f"--new-version={patched}",
            "patch",
        ]
        try:
            _ = check_call(cmd, stdout=PIPE, stderr=STDOUT)  # noqa: S603
        except CalledProcessError as cperror:
            if cperror.returncode != 1:
                error("Failed to run %r", " ".join(cmd))
        except FileNotFoundError:
            error(
                "Failed to run %r. Is `bump2version` installed?", " ".join(cmd)
            )
        return False


def _read_version(text: str, /) -> "Version":
    (group,) = findall(
        r"current_version = (\d+)\.(\d+)\.(\d+)$", text, flags=MULTILINE
    )
    major, minor, patch = map(int, group)
    return Version(major, minor, patch)


@dataclass(repr=False, frozen=True)
class Version:
    major: int
    minor: int
    patch: int

    def __repr__(self) -> str:
        return ".".join(map(str, astuple(self)))

    def __str__(self) -> str:
        return repr(self)

    def bump_major(self) -> "Version":
        return Version(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> "Version":
        return Version(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> "Version":
        return Version(major=self.major, minor=self.minor, patch=self.patch + 1)


if __name__ == "__main__":
    raise SystemExit(main())
