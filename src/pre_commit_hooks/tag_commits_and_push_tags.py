from argparse import ArgumentParser
from logging import basicConfig
from re import MULTILINE
from re import findall
from subprocess import PIPE  # noqa: S404
from subprocess import STDOUT  # noqa: S404
from subprocess import check_call  # noqa: S404
from subprocess import check_output  # noqa: S404
from sys import stdout


basicConfig(level="INFO", stream=stdout)


def main() -> int:
    parser = ArgumentParser()
    parser.add_argument("--setup-cfg", action="store_true")
    parser.add_argument("--max-count", type=int, default=10)
    args = parser.parse_args()
    return int(not _process(setup_cfg=args.setup_cfg, max_count=args.max_count))


def _process(*, setup_cfg: bool, max_count: int) -> bool:
    filename = "setup.cfg" if setup_cfg else ".bumpversion.cfg"
    for commit in _get_master_commits(max_count):
        if not _is_tagged(commit):
            version = _read_version(commit, filename)
            _tag_commit(version, commit)
    _push_tags()
    return True


def _get_master_commits(max_count: int, /) -> list[str]:
    _ = check_call(  # noqa: S603, S607
        ["git", "fetch", "--all"], stdout=PIPE, stderr=STDOUT
    )
    return (
        check_output(  # noqa: S603, S607
            ["git", "rev-list", "origin/master", f"--max-count={max_count}"],
            text=True,
        )
        .rstrip("\n")
        .splitlines()
    )


def _is_tagged(commit: str, /) -> bool:
    output = check_output(  # noqa: S603, S607
        ["git", "tag", "--points-at", commit], text=True
    ).rstrip("\n")
    return output != ""


def _read_version(commit: str, filename: str, /) -> str:
    output = check_output(  # noqa: S603, S607
        ["git", "show", f"{commit}:{filename}"], text=True
    )
    (version,) = findall(
        r"current_version = (\d+\.\d+\.\d+)$", output, flags=MULTILINE
    )
    return version


def _tag_commit(version: str, commit: str, /) -> None:
    _ = check_call(  # noqa: S603, S607
        ["git", "tag", "-a", version, commit, "-m", version],
        stdout=PIPE,
        stderr=STDOUT,
    )


def _push_tags() -> None:
    _ = check_call(  # noqa: S603, S607
        ["git", "push", "-u", "origin", "--tags"], stdout=PIPE, stderr=STDOUT
    )


if __name__ == "__main__":
    raise SystemExit(main())
