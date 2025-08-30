from __future__ import annotations

from typing import TYPE_CHECKING

from click import command
from git import Commit, GitCommandError, Repo
from loguru import logger
from utilities.tzlocal import LOCAL_TIME_ZONE_NAME
from utilities.whenever import WEEK, from_timestamp, get_now_local

from pre_commit_hooks.common import get_version

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from whenever import ZonedDateTime


@command()
def main() -> bool:
    """CLI for the `tag_commits` hook."""
    return _process()


def _process() -> bool:
    repo = Repo(".", search_parent_directories=True)
    tagged = {tag.commit.hexsha for tag in repo.tags}
    min_dt = get_now_local() - WEEK
    commits = reversed(list(repo.iter_commits(repo.refs["origin/master"])))
    return all(_process_commit(c, tagged, min_dt, repo) for c in commits)


def _process_commit(
    commit: Commit, tagged: AbstractSet[str], min_date: ZonedDateTime, repo: Repo, /
) -> bool:
    if (commit.hexsha in tagged) or (_get_date_time(commit) < min_date):
        return True
    _tag_commit(commit, repo)
    return False


def _get_date_time(commit: Commit, /) -> ZonedDateTime:
    return from_timestamp(commit.committed_date, time_zone=LOCAL_TIME_ZONE_NAME)


def _tag_commit(commit: Commit, repo: Repo, /) -> None:
    sha = commit.hexsha[:7]
    date = _get_date_time(commit)
    try:
        joined = commit.tree.join("pyproject.toml")
    except KeyError:
        logger.exception("`pyproject.toml` not found; failed to tag %r (%s)", sha, date)
        return
    text = joined.data_stream.read()
    version = get_version(text, desc=f"'pyproject.toml' @ {sha}")
    try:
        tag = repo.create_tag(str(version), ref=sha)
    except GitCommandError as error:
        logger.exception(
            "Failed to tag %r (%s) due to %r",
            sha,
            date,
            error.stderr.strip("\n").strip(),
        )
        return
    logger.info("Tagging %r (%s) as %r...", sha, date, str(version))
    _ = repo.remotes.origin.push(f"refs/tags/{tag.name}")


__all__ = ["main"]
