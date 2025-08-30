from __future__ import annotations

from typing import TYPE_CHECKING

import utilities.click
from click import command, option
from git import Commit, GitCommandError, Repo
from loguru import logger
from utilities.hashlib import md5_hash
from utilities.pathlib import get_repo_root
from utilities.tzlocal import LOCAL_TIME_ZONE_NAME
from utilities.whenever import from_timestamp, get_now_local
from whenever import DateTimeDelta, ZonedDateTime
from xdg_base_dirs import xdg_cache_home

from pre_commit_hooks.common import get_version

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

_RUN_EVERY: DateTimeDelta | None = None
_MAX_AGE: DateTimeDelta | None = None


@command()
@option(
    "--run-every",
    type=utilities.click.DateTimeDelta(),
    default=_RUN_EVERY,
    show_default=True,
)
@option(
    "--max-age",
    type=utilities.click.DateTimeDelta(),
    default=_MAX_AGE,
    show_default=True,
)
def main(
    *,
    run_every: DateTimeDelta | None = _RUN_EVERY,
    max_age: DateTimeDelta | None = _MAX_AGE,
) -> bool:
    """CLI for the `tag_commits` hook."""
    return _process(run_every=run_every, max_age=max_age)


def _process(
    *,
    run_every: DateTimeDelta | None = _RUN_EVERY,
    max_age: DateTimeDelta | None = _MAX_AGE,
) -> bool:
    if run_every is not None:
        last = _get_last_run()
        min_date_time = get_now_local() - run_every
        if (last is not None) and (min_date_time <= last):
            return True
    return _process_commits(max_age=max_age)


def _get_last_run() -> ZonedDateTime | None:
    hash_ = md5_hash(get_repo_root())
    path = xdg_cache_home().joinpath("tag-commits", hash_)
    try:
        text = path.read_text()
    except FileNotFoundError:
        return None
    try:
        return ZonedDateTime.parse_common_iso(text.strip("\n"))
    except ValueError:
        return None


def _process_commits(*, max_age: DateTimeDelta | None = None) -> bool:
    repo = Repo(".", search_parent_directories=True)
    tagged = {tag.commit.hexsha for tag in repo.tags}
    min_date_time = None if max_age is None else (get_now_local() - max_age)
    commits = reversed(list(repo.iter_commits(repo.refs["origin/master"])))
    results = [
        _process_commit(c, tagged, repo, min_date_time=min_date_time) for c in commits
    ]  # run all
    return all(results)


def _process_commit(
    commit: Commit,
    tagged: AbstractSet[str],
    repo: Repo,
    /,
    *,
    min_date_time: ZonedDateTime | None = None,
) -> bool:
    if (commit.hexsha in tagged) or (
        (min_date_time is not None) and (_get_date_time(commit) < min_date_time)
    ):
        return True
    try:
        _tag_commit(commit, repo)
    except GitCommandError:
        return False
    return True


def _get_date_time(commit: Commit, /) -> ZonedDateTime:
    return from_timestamp(commit.committed_date, time_zone=LOCAL_TIME_ZONE_NAME)


def _tag_commit(commit: Commit, repo: Repo, /) -> None:
    sha = commit.hexsha[:7]
    date = _get_date_time(commit)
    try:
        joined = commit.tree.join("pyproject.toml")
    except KeyError:
        logger.exception(f"`pyproject.toml` not found; failed to tag {sha!r} ({date})")
        return
    text = joined.data_stream.read()
    version = get_version(text, desc=f"'pyproject.toml' @ {sha}")
    try:
        tag = repo.create_tag(str(version), ref=sha)
    except GitCommandError as error:
        desc = error.stderr.strip("\n").strip()
        logger.exception(f"Failed to tag {sha!r} ({date}) due to {desc}")
        return
    logger.info(f"Tagging {sha!r} ({date}) as {str(version)!r}...")
    _ = repo.remotes.origin.push(f"refs/tags/{tag.name}")


__all__ = ["main"]
